// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {AbstractReactive} from "@reactive-lib-omni/base/AbstractReactive.sol";
import {ISystemContract} from "@reactive-lib-omni/interfaces/ISystemContract.sol";

/**
 * @title HalfwayReactive
 * @notice Cross-chain reactive arbitrage engine monitoring dual liquidity pools on Reactive Lasna.
 * @dev Subscribes to Sync events, calculates price spreads, bounded trade sizes, and dispatches callbacks.
 */
contract HalfwayReactive is AbstractReactive {
    // Sync(uint112,uint112) topic0
    uint256 public constant SYNC_TOPIC_0 = 0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1;
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant PRICE_PRECISION = 1e18;
    uint64 public constant CALLBACK_GAS_LIMIT = 300000;

    struct PoolConfig {
        uint256 chainId;
        address poolAddress;
        address executorAddress;
        uint8 decimals0;
        uint8 decimals1;
        uint16 feeBps; // e.g. 30 for 0.30%
        bool isRegistered;
    }

    struct PoolState {
        uint112 reserve0;
        uint112 reserve1;
        uint32 lastTimestamp;
        uint256 normalizedPrice; // Scaled to 1e18
    }

    address public owner;
    uint256 public thresholdBps; // Trigger spread threshold (net of fees)
    uint256 public safetyMarginBps; // Additional safety margin
    uint256 public maxTradeSize; // Maximum allowable trade size per leg
    uint256 public cooldownSeconds; // Minimum delay between executions
    uint256 public maxStalenessSeconds; // Maximum acceptable age for opposing pool price
    uint256 public executionTimeoutSeconds; // Callback execution deadline offset

    uint256 public lastExecutionTimestamp;
    uint256 public opportunityNonce;
    uint256 public totalOpportunitiesDetected;

    // Registry: key = keccak256(chainId, poolAddress)
    mapping(bytes32 => PoolConfig) public poolConfigs;
    mapping(bytes32 => PoolState) public poolStates;

    bytes32 public poolKeyA;
    bytes32 public poolKeyB;

    // Events
    event PoolRegistered(uint256 indexed chainId, address indexed poolAddress, address executor);
    event StrategyParametersUpdated(
        uint256 thresholdBps,
        uint256 safetyMarginBps,
        uint256 maxTradeSize,
        uint256 cooldownSeconds,
        uint256 maxStalenessSeconds
    );
    event OpportunityDetected(
        bytes32 indexed opportunityId,
        uint256 originChainId,
        uint256 priceA,
        uint256 priceB,
        uint256 spreadBps,
        uint256 optimalSize,
        uint256 timestamp
    );
    event CallbackDispatched(
        bytes32 indexed opportunityId,
        uint256 indexed targetChainId,
        address executor,
        bool isBuyToken0,
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 timestamp
    );

    error OnlyOwner();
    error PoolAlreadyRegistered();
    error PoolNotRegistered();
    error InvalidConfiguration();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(
        uint256 thresholdBps_,
        uint256 safetyMarginBps_,
        uint256 maxTradeSize_,
        uint256 cooldownSeconds_,
        uint256 maxStalenessSeconds_
    ) payable {
        owner = msg.sender;
        thresholdBps = thresholdBps_;
        safetyMarginBps = safetyMarginBps_;
        maxTradeSize = maxTradeSize_;
        cooldownSeconds = cooldownSeconds_;
        maxStalenessSeconds = maxStalenessSeconds_;
        executionTimeoutSeconds = 120; // 2 minutes execution window
    }

    /**
     * @notice Registers a target pool, executor, and subscribes to its Sync events on origin chain.
     */
    function registerPool(
        uint256 chainId_,
        address poolAddress_,
        address executorAddress_,
        uint8 decimals0_,
        uint8 decimals1_,
        uint16 feeBps_
    ) external onlyOwner {
        bytes32 key = keccak256(abi.encodePacked(chainId_, poolAddress_));
        if (poolConfigs[key].isRegistered) revert PoolAlreadyRegistered();

        poolConfigs[key] = PoolConfig({
            chainId: chainId_,
            poolAddress: poolAddress_,
            executorAddress: executorAddress_,
            decimals0: decimals0_,
            decimals1: decimals1_,
            feeBps: feeBps_,
            isRegistered: true
        });

        if (poolKeyA == bytes32(0)) {
            poolKeyA = key;
        } else if (poolKeyB == bytes32(0)) {
            poolKeyB = key;
        }

        // Subscribe to Sync events via Reactive Omni System contract
        SYSTEM.subscribe(chainId_, poolAddress_, SYNC_TOPIC_0, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);

        emit PoolRegistered(chainId_, poolAddress_, executorAddress_);
    }

    /**
     * @notice Reactive execution entrypoint invoked exclusively by the Reactive System contract.
     * @param log_ Encoded log record originating from subscribed pool.
     */
    function react(LogRecord calldata log_) external override onlySystem {
        bytes32 incomingKey = keccak256(abi.encodePacked(log_.chainId, log_.contractAddress));
        PoolConfig memory originConfig = poolConfigs[incomingKey];
        if (!originConfig.isRegistered) return;

        // Decode reserves from Sync event: (uint112 reserve0, uint112 reserve1)
        (uint112 r0, uint112 r1) = abi.decode(log_.data, (uint112, uint112));
        if (r0 == 0 || r1 == 0) return;

        // Calculate normalized price: (r1 * 1e18) / r0, adjusting for token decimals
        uint256 price = _calculateNormalizedPrice(r0, r1, originConfig.decimals0, originConfig.decimals1);
        poolStates[incomingKey] = PoolState({
            reserve0: r0, reserve1: r1, lastTimestamp: uint32(block.timestamp % 2 ** 32), normalizedPrice: price
        });

        // Evaluate opportunity against paired pool
        bytes32 peerKey = incomingKey == poolKeyA ? poolKeyB : poolKeyA;
        PoolConfig memory peerConfig = poolConfigs[peerKey];
        if (!peerConfig.isRegistered) return;

        PoolState memory peerState = poolStates[peerKey];
        if (peerState.reserve0 == 0 || peerState.reserve1 == 0) return;

        _evaluateOpportunity(originConfig, poolStates[incomingKey], peerConfig, peerState, log_);

        // Cover any accumulated system debt using contract lREACT reserves
        _coverDebt();
    }

    function _evaluateOpportunity(
        PoolConfig memory confOrigin,
        PoolState memory stateOrigin,
        PoolConfig memory confPeer,
        PoolState memory statePeer,
        LogRecord calldata log_
    ) internal {
        // Cooldown check (only if an execution already occurred)
        if (lastExecutionTimestamp != 0 && block.timestamp < lastExecutionTimestamp + cooldownSeconds) return;

        // Staleness check on peer pool
        if (block.timestamp > statePeer.lastTimestamp + maxStalenessSeconds) return;

        uint256 priceOrigin = stateOrigin.normalizedPrice;
        uint256 pricePeer = statePeer.normalizedPrice;
        if (priceOrigin == 0 || pricePeer == 0) return;

        // Determine price gap
        bool isOriginHigher = priceOrigin > pricePeer;
        uint256 diff = isOriginHigher ? priceOrigin - pricePeer : pricePeer - priceOrigin;
        uint256 basePrice = isOriginHigher ? pricePeer : priceOrigin;
        uint256 spreadBps = (diff * BPS_DENOMINATOR) / basePrice;

        // Total fee hurdle: Fee(origin) + Fee(peer) + SafetyMargin
        uint256 totalHurdleBps = uint256(confOrigin.feeBps) + uint256(confPeer.feeBps) + safetyMarginBps;
        if (spreadBps <= totalHurdleBps + thresholdBps) return;

        uint256 netSpreadBps = spreadBps - totalHurdleBps;

        // Optimal trade size calculation (closed-form bounded optimum)
        uint256 optimalSize = _calculateOptimalSize(stateOrigin, statePeer, netSpreadBps);
        if (optimalSize == 0) return;

        bytes32 opportunityId =
            keccak256(abi.encodePacked(block.timestamp, log_.chainId, log_.contractAddress, opportunityNonce++));
        lastExecutionTimestamp = block.timestamp;
        totalOpportunitiesDetected++;

        emit OpportunityDetected(
            opportunityId, log_.chainId, priceOrigin, pricePeer, spreadBps, optimalSize, block.timestamp
        );

        // Dispatch Callbacks to both executors
        _dispatchCallbacks(opportunityId, confOrigin, stateOrigin, confPeer, statePeer, isOriginHigher, optimalSize);
    }

    function _dispatchCallbacks(
        bytes32 opportunityId,
        PoolConfig memory confOrigin,
        PoolState memory stateOrigin,
        PoolConfig memory confPeer,
        PoolState memory statePeer,
        bool isOriginHigher,
        uint256 size
    ) internal {
        uint256 deadline = block.timestamp + executionTimeoutSeconds;

        // If Origin is higher: token0 is more expensive on Origin -> Sell token0 on Origin (Buy token1), Buy token0 on Peer
        bool originBuyToken0 = !isOriginHigher;
        bool peerBuyToken0 = isOriginHigher;

        // Calculate minimum expected outputs with 1.0% slippage tolerance
        uint256 minOutOrigin = _estimateMinOut(stateOrigin, originBuyToken0, size);
        uint256 minOutPeer = _estimateMinOut(statePeer, peerBuyToken0, size);

        // Payload reserves the first address parameter for proxy authentication injection
        bytes memory originPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)",
            address(0),
            abi.encode(opportunityId, originBuyToken0, size, minOutOrigin, deadline)
        );

        bytes memory peerPayload = abi.encodeWithSignature(
            "executeCallback(address,bytes)",
            address(0),
            abi.encode(opportunityId, peerBuyToken0, size, minOutPeer, deadline)
        );

        // Dispatch via Reactive Omni requestCallbackV_1_0
        SYSTEM.requestCallbackV_1_0(
            ISystemContract.CallbackConfiguration_V_1_0({
                chainId: confOrigin.chainId,
                recipient: confOrigin.executorAddress,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: originPayload
            })
        );
        emit CallbackDispatched(
            opportunityId,
            confOrigin.chainId,
            confOrigin.executorAddress,
            originBuyToken0,
            size,
            minOutOrigin,
            block.timestamp
        );

        SYSTEM.requestCallbackV_1_0(
            ISystemContract.CallbackConfiguration_V_1_0({
                chainId: confPeer.chainId,
                recipient: confPeer.executorAddress,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: peerPayload
            })
        );
        emit CallbackDispatched(
            opportunityId, confPeer.chainId, confPeer.executorAddress, peerBuyToken0, size, minOutPeer, block.timestamp
        );
    }

    function _calculateOptimalSize(PoolState memory stateA, PoolState memory stateB, uint256 netSpreadBps)
        internal
        view
        returns (uint256)
    {
        // Closed-form optimum: Delta x ~= (netSpreadBps / 20000) * min(r0A, r0B)
        uint256 minReserve = stateA.reserve0 < stateB.reserve0 ? stateA.reserve0 : stateB.reserve0;
        uint256 theoreticalSize = (minReserve * netSpreadBps) / (2 * BPS_DENOMINATOR);

        if (theoreticalSize > maxTradeSize) {
            return maxTradeSize;
        }
        return theoreticalSize;
    }

    function _estimateMinOut(PoolState memory state, bool isBuyToken0, uint256 amountIn)
        internal
        pure
        returns (uint256)
    {
        uint256 rIn = isBuyToken0 ? state.reserve1 : state.reserve0;
        uint256 rOut = isBuyToken0 ? state.reserve0 : state.reserve1;
        if (rIn == 0 || rOut == 0) return 0;

        uint256 amountInWithFee = amountIn * 9970; // 0.30% fee
        uint256 numerator = amountInWithFee * rOut;
        uint256 denominator = (rIn * 10000) + amountInWithFee;
        uint256 expectedOut = (numerator * 9900) / (denominator * 10000);

        return expectedOut;
    }

    function _calculateNormalizedPrice(uint112 r0, uint112 r1, uint8 dec0, uint8 dec1) internal pure returns (uint256) {
        // Price = (r1 / 10^dec1) / (r0 / 10^dec0) * 1e18 = (r1 * 10^dec0 * 1e18) / (r0 * 10^dec1)
        uint256 num = uint256(r1) * (10 ** dec0) * PRICE_PRECISION;
        uint256 den = uint256(r0) * (10 ** dec1);
        return num / den;
    }

    function setStrategyParameters(
        uint256 thresholdBps_,
        uint256 safetyMarginBps_,
        uint256 maxTradeSize_,
        uint256 cooldownSeconds_,
        uint256 maxStalenessSeconds_
    ) external onlyOwner {
        thresholdBps = thresholdBps_;
        safetyMarginBps = safetyMarginBps_;
        maxTradeSize = maxTradeSize_;
        cooldownSeconds = cooldownSeconds_;
        maxStalenessSeconds = maxStalenessSeconds_;

        emit StrategyParametersUpdated(
            thresholdBps_, safetyMarginBps_, maxTradeSize_, cooldownSeconds_, maxStalenessSeconds_
        );
    }
}
