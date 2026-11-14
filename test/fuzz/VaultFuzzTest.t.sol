// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfPair} from "../../src/amm/HalfPair.sol";
import {HalfwayExecutor} from "../../src/vault/HalfwayExecutor.sol";
import {MockCallbackProxy} from "../mocks/MockCallbackProxy.sol";

contract VaultFuzzTest is Test {
    MockERC20 public token0;
    MockERC20 public token1;
    HalfPair public pool;
    MockCallbackProxy public proxy;
    HalfwayExecutor public executor;

    address public user = address(0xABCD);
    address public reactiveLasna = address(0x9999);

    function setUp() public {
        token0 = new MockERC20("Token 0", "TK0", 18, address(this));
        token1 = new MockERC20("Token 1", "TK1", 18, address(this));

        if (address(token0) > address(token1)) {
            (token0, token1) = (token1, token0);
        }

        pool = new HalfPair(address(token0), address(token1));
        proxy = new MockCallbackProxy();

        executor = new HalfwayExecutor(
            payable(address(proxy)), reactiveLasna, address(token0), address(token1), address(pool), address(this)
        );

        token0.mint(address(this), 1_000_000 ether);
        token1.mint(address(this), 1_000_000 ether);

        // Bootstrap vault with initial liquidity so MINIMUM_LIQUIDITY is seeded
        token0.approve(address(executor), type(uint256).max);
        token1.approve(address(executor), type(uint256).max);
        executor.deposit(100 ether, 100 ether, address(this));

        token0.mint(user, 1_000_000 ether);
        token1.mint(user, 1_000_000 ether);

        vm.startPrank(user);
        token0.approve(address(executor), type(uint256).max);
        token1.approve(address(executor), type(uint256).max);
        vm.stopPrank();
    }

    function testFuzz_DepositAndWithdrawSolvency(uint128 amount0, uint128 amount1) public {
        // Bound inputs to avoid overflow and ensure proportional ratio close to 1:1
        vm.assume(amount0 >= 100_000 && amount0 <= 10_000 ether);
        // Keep amount1 proportional to preserve pool balance in test
        uint256 amount1Bounded = amount0;

        vm.startPrank(user);
        uint256 shares = executor.deposit(amount0, amount1Bounded, user);
        assertGt(shares, 0);

        (uint256 out0, uint256 out1) = executor.withdraw(shares, user);
        vm.stopPrank();

        // Rounding in integer division cannot lose more than 2 wei per asset
        assertApproxEqAbs(out0, amount0, 2);
        assertApproxEqAbs(out1, amount1Bounded, 2);
    }

    function testFuzz_ShareInflationProtection(uint128 attackerDeposit, uint128 donation) public {
        // Test in isolated fresh vault without bootstrap
        HalfwayExecutor freshVault = new HalfwayExecutor(
            payable(address(proxy)), reactiveLasna, address(token0), address(token1), address(pool), address(this)
        );

        vm.assume(attackerDeposit >= 10_000 && attackerDeposit <= 1 ether);
        vm.assume(donation >= 10_000 && donation <= 100 ether);

        address attacker = address(0xBAD);
        token0.mint(attacker, attackerDeposit + donation);
        token1.mint(attacker, attackerDeposit + donation);

        vm.startPrank(attacker);
        token0.approve(address(freshVault), type(uint256).max);
        token1.approve(address(freshVault), type(uint256).max);

        // Attacker creates first small deposit
        freshVault.deposit(attackerDeposit, attackerDeposit, attacker);

        // Attacker attempts inflation donation directly to vault
        token0.transfer(address(freshVault), donation);
        token1.transfer(address(freshVault), donation);
        vm.stopPrank();

        // Victim deposits standard amount
        uint256 victimAmount = 10 ether;
        vm.startPrank(user);
        token0.approve(address(freshVault), type(uint256).max);
        token1.approve(address(freshVault), type(uint256).max);
        uint256 victimShares = freshVault.deposit(victimAmount, victimAmount, user);
        vm.stopPrank();

        // Victim MUST receive non-zero shares (inflation attack neutralized by MINIMUM_LIQUIDITY)
        assertGt(victimShares, 0);
    }
}
