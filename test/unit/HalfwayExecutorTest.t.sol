// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfPair} from "../../src/amm/HalfPair.sol";
import {HalfwayExecutor} from "../../src/vault/HalfwayExecutor.sol";
import {MockCallbackProxy} from "../mocks/MockCallbackProxy.sol";

contract HalfwayExecutorTest is Test {
    MockERC20 public token0;
    MockERC20 public token1;
    HalfPair public pool;
    MockCallbackProxy public proxy;
    HalfwayExecutor public executor;

    address public reactiveLasna = address(0x9999);
    address public alice = address(0xAAAA);
    address public bob = address(0xBBBB);

    function setUp() public {
        token0 = new MockERC20("Token 0", "TK0", 18, address(this));
        token1 = new MockERC20("Token 1", "TK1", 18, address(this));

        // Ensure token0 < token1 address order
        if (address(token0) > address(token1)) {
            (token0, token1) = (token1, token0);
        }

        pool = new HalfPair(address(token0), address(token1));
        proxy = new MockCallbackProxy();

        executor = new HalfwayExecutor(
            payable(address(proxy)), reactiveLasna, address(token0), address(token1), address(pool), address(this)
        );

        // Seed pool liquidity: 1000 token0 and 1000 token1
        token0.mint(address(this), 10_000 ether);
        token1.mint(address(this), 10_000 ether);

        token0.transfer(address(pool), 1000 ether);
        token1.transfer(address(pool), 1000 ether);
        pool.mint(address(this));

        // Distribute tokens to Alice and Bob
        token0.mint(alice, 100 ether);
        token1.mint(alice, 100 ether);
        token0.mint(bob, 100 ether);
        token1.mint(bob, 100 ether);

        vm.prank(alice);
        token0.approve(address(executor), type(uint256).max);
        vm.prank(alice);
        token1.approve(address(executor), type(uint256).max);

        vm.prank(bob);
        token0.approve(address(executor), type(uint256).max);
        vm.prank(bob);
        token1.approve(address(executor), type(uint256).max);
    }

    function test_DepositAndWithdraw() public {
        vm.prank(alice);
        uint256 shares = executor.deposit(10 ether, 10 ether, alice);
        assertGt(shares, 0);
        assertEq(executor.balanceOf(alice), shares);

        // Alice withdraws half her shares
        vm.prank(alice);
        (uint256 out0, uint256 out1) = executor.withdraw(shares / 2, alice);
        assertApproxEqAbs(out0, 5 ether, 1000);
        assertApproxEqAbs(out1, 5 ether, 1000);
    }

    function test_ExitGuarantee_WithdrawWhenPaused() public {
        vm.prank(alice);
        uint256 shares = executor.deposit(10 ether, 10 ether, alice);

        // Admin pauses executor
        executor.pause();
        assertTrue(executor.paused());

        // New deposits must fail when paused
        vm.expectRevert();
        vm.prank(alice);
        executor.deposit(1 ether, 1 ether, alice);

        // Withdraw MUST SUCCEED when paused (Exit guarantee)
        vm.prank(alice);
        (uint256 out0, uint256 out1) = executor.withdraw(shares, alice);
        assertGt(out0, 0);
        assertGt(out1, 0);
    }

    function test_ReplayProtection() public {
        // Alice deposits vault inventory
        vm.prank(alice);
        executor.deposit(50 ether, 50 ether, alice);

        bytes32 opportunityId = keccak256("OPP_1");
        uint256 amountIn = 1 ether;
        (uint112 r0, uint112 r1,) = pool.getReserves();
        uint256 expectedOut = pool.getAmountOut(amountIn, r1, r0);
        uint256 minOut = (expectedOut * 9900) / 10000;
        uint256 deadline = block.timestamp + 300;

        bytes memory rawPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)", address(0), abi.encode(opportunityId, true, amountIn, minOut, deadline)
        );

        // First execution via authorized proxy
        proxy.relayCallback(address(executor), reactiveLasna, rawPayload);
        assertTrue(executor.executedOpportunities(opportunityId));

        // Second execution MUST revert with OpportunityAlreadyExecuted
        vm.expectRevert();
        proxy.relayCallback(address(executor), reactiveLasna, rawPayload);
    }

    function test_UnauthorizedCallerRejection() public {
        bytes32 opportunityId = keccak256("OPP_UNAUTH");
        bytes memory rawPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)",
            reactiveLasna,
            abi.encode(opportunityId, true, 1 ether, 0.9 ether, block.timestamp + 100)
        );

        // Direct call from unauthorized attacker (not proxy)
        vm.expectRevert();
        executor.executeCallback(reactiveLasna, rawPayload);
    }

    function test_UnauthorizedReactiveSenderRejection() public {
        bytes32 opportunityId = keccak256("OPP_BAD_SENDER");
        bytes memory rawPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)",
            address(0),
            abi.encode(opportunityId, true, 1 ether, 0.9 ether, block.timestamp + 100)
        );

        address attackerReactive = address(0x6666);
        // Proxy relays from untrusted reactive sender
        vm.expectRevert();
        proxy.relayCallback(address(executor), attackerReactive, rawPayload);
    }

    function test_DeadlineExpiredSkipsLeg() public {
        vm.prank(alice);
        executor.deposit(10 ether, 10 ether, alice);

        bytes32 opportunityId = keccak256("OPP_EXPIRED");
        uint256 pastDeadline = block.timestamp - 1;

        bytes memory rawPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)",
            address(0),
            abi.encode(opportunityId, true, 1 ether, 0.9 ether, pastDeadline)
        );

        proxy.relayCallback(address(executor), reactiveLasna, rawPayload);
        assertEq(executor.consecutiveFailures(), 1);
    }

    function test_CircuitBreakerPausesAfterConsecutiveFailures() public {
        vm.prank(alice);
        executor.deposit(10 ether, 10 ether, alice);

        uint256 maxFails = executor.maxConsecutiveFailures();

        for (uint256 i = 0; i < maxFails; i++) {
            bytes32 oppId = keccak256(abi.encodePacked("FAIL_", i));
            bytes memory rawPayload = abi.encodeWithSignature(
                "executeCallback(address,bytes)",
                address(0),
                abi.encode(oppId, true, 1 ether, 0.9 ether, block.timestamp - 1) // expired deadline
            );
            proxy.relayCallback(address(executor), reactiveLasna, rawPayload);
        }

        assertTrue(executor.paused());
    }

    function test_AdminParameterBounds() public {
        // Slippage cannot exceed 500 bps (5.0%)
        vm.expectRevert();
        executor.setParameters(1 ether, 501, 5);

        // Max failures cannot be 0 or > 50
        vm.expectRevert();
        executor.setParameters(1 ether, 100, 0);

        vm.expectRevert();
        executor.setParameters(1 ether, 100, 51);

        // Valid update succeeds
        executor.setParameters(5 ether, 200, 10);
        assertEq(executor.maxTradeSize(), 5 ether);
        assertEq(executor.maxSlippageBps(), 200);
        assertEq(executor.maxConsecutiveFailures(), 10);
    }
}
