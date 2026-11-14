// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {Test} from "forge-std/Test.sol";
import {HalfwayReactive} from "../../src/reactive/HalfwayReactive.sol";
import {MockSystemContract} from "../mocks/MockSystemContract.sol";
import {IReactive} from "@reactive-lib-omni/interfaces/IReactive.sol";
import {ISystemContract} from "@reactive-lib-omni/interfaces/ISystemContract.sol";

contract HalfwayReactiveTest is Test {
    MockSystemContract public systemContract;
    HalfwayReactive public reactive;

    address public constant SYSTEM_ADDR = 0x8888888888888888888888888888888888888888;
    address public poolA = address(0xAAAA);
    address public poolB = address(0xBBBB);
    address public executorA = address(0x1111);
    address public executorB = address(0x2222);

    uint256 public constant CHAIN_A = 84532; // Base Sepolia
    uint256 public constant CHAIN_B = 1301; // Unichain Sepolia

    function setUp() public {
        // Deploy MockSystemContract and etch to 0x888...888
        MockSystemContract mockSys = new MockSystemContract();
        vm.etch(SYSTEM_ADDR, address(mockSys).code);
        systemContract = MockSystemContract(payable(SYSTEM_ADDR));

        reactive = new HalfwayReactive(
            50, // thresholdBps: 50 bps (0.50%)
            10, // safetyMarginBps: 10 bps
            5 ether, // maxTradeSize: 5 ether
            5, // cooldown: 5 seconds
            60 // maxStaleness: 60 seconds
        );

        // Register Pool A and Pool B
        reactive.registerPool(CHAIN_A, poolA, executorA, 18, 18, 30);
        reactive.registerPool(CHAIN_B, poolB, executorB, 18, 18, 30);
    }

    function test_SubscriptionsCreated() public view {
        assertEq(systemContract.getSubscriptionCount(), 2);
    }

    function test_ReactUpdatesReservesAndPrices() public {
        // Construct Sync log for Pool A: (100 ether, 100 ether) -> price = 1.0 * 1e18
        IReactive.LogRecord memory logA = IReactive.LogRecord({
            chainId: CHAIN_A,
            contractAddress: poolA,
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
        reactive.react(logA);

        bytes32 keyA = keccak256(abi.encodePacked(CHAIN_A, poolA));
        (uint112 r0, uint112 r1, uint32 ts, uint256 price) = reactive.poolStates(keyA);
        assertEq(r0, 100 ether);
        assertEq(r1, 100 ether);
        assertGt(ts, 0);
        assertEq(price, 1e18);
    }

    function test_OpportunityDetectionAndCallbackDispatch() public {
        // 1. Initialise Pool A at price 1.00 (100 ether, 100 ether)
        IReactive.LogRecord memory logA = IReactive.LogRecord({
            chainId: CHAIN_A,
            contractAddress: poolA,
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
        reactive.react(logA);

        // 2. Shock Pool B price to 1.10 (90 ether, 99 ether) -> Spread ~10% (1000 bps)
        // Fees: 30 + 30 + 10 = 70 bps. Threshold: 50 bps. Net spread > threshold!
        IReactive.LogRecord memory logB = IReactive.LogRecord({
            chainId: CHAIN_B,
            contractAddress: poolB,
            topic0: reactive.SYNC_TOPIC_0(),
            topic1: 0,
            topic2: 0,
            topic3: 0,
            data: abi.encode(uint112(90 ether), uint112(99 ether)),
            blockNumber: 2000,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });

        vm.prank(SYSTEM_ADDR);
        reactive.react(logB);

        // Verify callbacks were requested to both executors!
        assertEq(systemContract.getRequestedCallbackCount(), 2);
        assertEq(reactive.totalOpportunitiesDetected(), 1);

        ISystemContract.CallbackConfiguration_V_1_0 memory cbA = systemContract.getRequestedCallback(0);
        ISystemContract.CallbackConfiguration_V_1_0 memory cbB = systemContract.getRequestedCallback(1);

        assertEq(cbA.chainId, CHAIN_B);
        assertEq(cbA.recipient, executorB);
        assertEq(cbB.chainId, CHAIN_A);
        assertEq(cbB.recipient, executorA);
    }

    function test_CooldownSuppressesRapidTriggers() public {
        // Setup initial prices
        IReactive.LogRecord memory logA = IReactive.LogRecord({
            chainId: CHAIN_A,
            contractAddress: poolA,
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
        reactive.react(logA);

        // Trigger opportunity 1
        IReactive.LogRecord memory logB1 = IReactive.LogRecord({
            chainId: CHAIN_B,
            contractAddress: poolB,
            topic0: reactive.SYNC_TOPIC_0(),
            topic1: 0,
            topic2: 0,
            topic3: 0,
            data: abi.encode(uint112(90 ether), uint112(100 ether)),
            blockNumber: 2000,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });

        vm.prank(SYSTEM_ADDR);
        reactive.react(logB1);
        assertEq(reactive.totalOpportunitiesDetected(), 1);

        // Immediate subsequent shock within cooldown (cooldown = 5s, time elapsed = 0)
        IReactive.LogRecord memory logB2 = IReactive.LogRecord({
            chainId: CHAIN_B,
            contractAddress: poolB,
            topic0: reactive.SYNC_TOPIC_0(),
            topic1: 0,
            topic2: 0,
            topic3: 0,
            data: abi.encode(uint112(85 ether), uint112(105 ether)),
            blockNumber: 2001,
            opCode: 0,
            blockHash: 0,
            txHash: 0,
            logIndex: 0
        });

        vm.prank(SYSTEM_ADDR);
        reactive.react(logB2);

        // Must still be 1 (cooldown suppressed the 2nd trigger)
        assertEq(reactive.totalOpportunitiesDetected(), 1);

        // Advance time past cooldown
        vm.warp(block.timestamp + 6);
        vm.prank(SYSTEM_ADDR);
        reactive.react(logB2);

        // Now trigger count increases to 2
        assertEq(reactive.totalOpportunitiesDetected(), 2);
    }
}
