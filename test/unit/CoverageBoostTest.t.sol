// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {MockERC20} from "../../src/tokens/MockERC20.sol";
import {HalfPair} from "../../src/amm/HalfPair.sol";
import {HalfwayExecutor} from "../../src/vault/HalfwayExecutor.sol";
import {HalfwayReactive} from "../../src/reactive/HalfwayReactive.sol";
import {MockSystemContract} from "../mocks/MockSystemContract.sol";
import {MockCallbackProxy} from "../mocks/MockCallbackProxy.sol";
import {IReactive} from "@reactive-lib-omni/interfaces/IReactive.sol";

contract CoverageBoostTest is Test {
    address public constant SYSTEM_ADDR = 0x8888888888888888888888888888888888888888;

    MockERC20 public token0;
    MockERC20 public token1;
    HalfPair public pool;
    MockCallbackProxy public proxy;
    HalfwayExecutor public executor;
    MockSystemContract public systemContract;
    HalfwayReactive public reactive;

    address public user = address(0x5555);

    function setUp() public {
        MockSystemContract mockSys = new MockSystemContract();
        vm.etch(SYSTEM_ADDR, address(mockSys).code);
        systemContract = MockSystemContract(payable(SYSTEM_ADDR));

        token0 = new MockERC20("Token 0", "TK0", 18, address(this));
        token1 = new MockERC20("Token 1", "TK1", 18, address(this));

        if (address(token0) > address(token1)) {
            (token0, token1) = (token1, token0);
        }

        pool = new HalfPair(address(token0), address(token1));
        proxy = new MockCallbackProxy();

        executor = new HalfwayExecutor(
            payable(address(proxy)), address(this), address(token0), address(token1), address(pool), address(this)
        );

        reactive = new HalfwayReactive(
            50, // threshold: 50 bps
            10, // safety margin: 10 bps
            1 ether, // maxTradeSize: 1 ether
            5, // cooldown: 5s
            60 // staleness: 60s
        );

        token0.mint(address(this), 10_000 ether);
        token1.mint(address(this), 10_000 ether);
        token0.transfer(address(pool), 100 ether);
        token1.transfer(address(pool), 100 ether);
        pool.mint(address(this));
    }

    function test_MockERC20_FaucetAndMint() public {
        vm.prank(user);
        token0.faucet(500 ether);
        assertEq(token0.balanceOf(user), 500 ether);

        vm.prank(user);
        vm.expectRevert();
        token0.faucet(1001 ether); // Exceeds limit

        assertEq(token0.decimals(), 18);
    }

    function test_Executor_UnpauseAndSetParameters() public {
        executor.pause();
        assertTrue(executor.paused());
        executor.unpause();
        assertFalse(executor.paused());

        executor.setParameters(20 ether, 300, 10);
        assertEq(executor.maxTradeSize(), 20 ether);
    }

    function test_Executor_ZeroInputsRevert() public {
        vm.expectRevert(HalfwayExecutor.ZeroAmount.selector);
        executor.deposit(0, 10 ether, address(this));

        vm.expectRevert(HalfwayExecutor.ZeroAmount.selector);
        executor.deposit(10 ether, 0, address(this));

        vm.expectRevert(HalfwayExecutor.ZeroAddress.selector);
        executor.deposit(1 ether, 1 ether, address(0));

        vm.expectRevert(HalfwayExecutor.ZeroAmount.selector);
        executor.withdraw(0, address(this));

        vm.expectRevert(HalfwayExecutor.ZeroAddress.selector);
        executor.withdraw(10, address(0));
    }

    function test_Reactive_InverseDirectionAndCappedSize() public {
        address poolA = address(0xAAAA);
        address poolB = address(0xBBBB);

        reactive.registerPool(84532, poolA, address(0x1), 18, 18, 30);
        reactive.registerPool(1301, poolB, address(0x2), 18, 18, 30);

        // Initialise Pool B first (at 100 ether, 100 ether)
        IReactive.LogRecord memory logB = IReactive.LogRecord({
            chainId: 1301,
            contractAddress: poolB,
            topic0: reactive.SYNC_TOPIC_0(),
            topic1: 0,
            topic2: 0,
            topic3: 0,
            data: abi.encode(uint112(100 ether), uint112(100 ether)),
            blockNumber: 1000,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });
        vm.prank(SYSTEM_ADDR);
        reactive.react(logB);

        // Shock Pool A: price increases on A (origin is higher)
        IReactive.LogRecord memory logA = IReactive.LogRecord({
            chainId: 84532,
            contractAddress: poolA,
            topic0: reactive.SYNC_TOPIC_0(),
            topic1: 0,
            topic2: 0,
            topic3: 0,
            data: abi.encode(uint112(80 ether), uint112(110 ether)),
            blockNumber: 2000,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });
        vm.prank(SYSTEM_ADDR);
        reactive.react(logA);

        assertGt(reactive.totalOpportunitiesDetected(), 0);

        // Update strategy parameters
        reactive.setStrategyParameters(60, 15, 2 ether, 10, 120);
        assertEq(reactive.thresholdBps(), 60);
        assertEq(reactive.safetyMarginBps(), 15);
    }
}
