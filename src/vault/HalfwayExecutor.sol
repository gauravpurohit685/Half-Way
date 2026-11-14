// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AbstractCallback} from "@reactive-lib-omni/base/AbstractCallback.sol";
import {IPayable} from "@reactive-lib-omni/interfaces/IPayable.sol";
import {HalfPair} from "../amm/HalfPair.sol";

/**
 * @title HalfwayExecutor
 * @notice Non-custodial cross-chain price-gap capture vault and execution engine.
 * @dev Authenticates Reactive Lasna callbacks via AbstractCallback and CallbackProxy verification.
 */
contract HalfwayExecutor is AbstractCallback, Ownable2Step, Pausable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    /// @notice Vault core token immutables
    address public immutable token0;
    address public immutable token1;
    HalfPair public immutable pool;

    uint256 public constant MINIMUM_LIQUIDITY = 1000;
    uint256 public constant BPS_DENOMINATOR = 10000;

    /// @notice Strategy bounds (enforced in admin setters)
    uint256 public constant ABSOLUTE_MAX_SLIPPAGE_BPS = 500; // 5.0%
    uint256 public constant MIN_COOLDOWN_SECONDS = 1;
    uint256 public constant MAX_COOLDOWN_SECONDS = 3600;

    /// @notice Configurable parameters within bounded ranges
    uint256 public maxTradeSize;
    uint256 public maxSlippageBps;
    uint256 public maxConsecutiveFailures;
    uint256 public consecutiveFailures;

    /// @notice LP Accounting
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    /// @notice Replay protection
    mapping(bytes32 => bool) public executedOpportunities;

    /// @notice Exposure tracking for partial fills
    mapping(bytes32 => uint256) public unhedgedExposure;

    // Custom Errors
    error ZeroAddress();
    error ZeroAmount();
    error InsufficientLiquidityMinted();
    error InsufficientLiquidityBurned();
    error FeeOnTransferUnsupported();
    error OpportunityAlreadyExecuted(bytes32 opportunityId);
    error UnauthorizedCallbackCaller(address caller);
    error ParameterOutOfBounds(string parameter);
    error CircuitBreakerTripped(uint256 failures);

    // Events
    event Deposited(address indexed user, uint256 amount0, uint256 amount1, uint256 shares, uint256 timestamp);
    event Withdrawn(address indexed user, uint256 shares, uint256 amount0, uint256 amount1, uint256 timestamp);
    event LegExecuted(
        bytes32 indexed opportunityId, bool isBuyToken0, uint256 amountIn, uint256 amountOut, uint256 timestamp
    );
    event LegSkipped(bytes32 indexed opportunityId, string reason, uint256 timestamp);
    event LegFailed(bytes32 indexed opportunityId, string reason, uint256 timestamp);
    event ParametersUpdated(uint256 maxTradeSize, uint256 maxSlippageBps, uint256 maxConsecutiveFailures);

    /**
     * @notice Constructor initializing immutable tokens, pool, and callback proxy.
     * @param callbackProxy_ Official Reactive callback proxy address on this chain.
     * @param callbackSender_ HalfwayReactive contract address on Reactive Lasna.
     * @param token0_ Token0 address.
     * @param token1_ Token1 address.
     * @param pool_ HalfPair AMM address.
     * @param initialOwner_ Initial owner address for 2-step governance.
     */
    constructor(
        address payable callbackProxy_,
        address callbackSender_,
        address token0_,
        address token1_,
        address pool_,
        address initialOwner_
    ) AbstractCallback(IPayable(callbackProxy_), callbackSender_) Ownable(initialOwner_) {
        if (token0_ == address(0) || token1_ == address(0) || pool_ == address(0)) {
            revert ZeroAddress();
        }
        token0 = token0_;
        token1 = token1_;
        pool = HalfPair(pool_);

        maxTradeSize = 10 ether;
        maxSlippageBps = 100; // 1.0%
        maxConsecutiveFailures = 5;
    }

    // ==========================================
    // NON-CUSTODIAL VAULT (DEPOSIT / WITHDRAW)
    // ==========================================

    /**
     * @notice Deposits token0 and token1 into the vault in exchange for LP shares.
     * @param amount0 Desired amount of token0.
     * @param amount1 Desired amount of token1.
     * @param to Recipient of the minted shares.
     * @return shares Amount of shares minted.
     */
    function deposit(uint256 amount0, uint256 amount1, address to)
        external
        nonReentrant
        whenNotPaused
        returns (uint256 shares)
    {
        if (amount0 == 0 || amount1 == 0) revert ZeroAmount();
        if (to == address(0)) revert ZeroAddress();

        uint256 bal0Before = IERC20(token0).balanceOf(address(this));
        uint256 bal1Before = IERC20(token1).balanceOf(address(this));

        IERC20(token0).safeTransferFrom(msg.sender, address(this), amount0);
        IERC20(token1).safeTransferFrom(msg.sender, address(this), amount1);

        // forge-lint: disable-next-line(incorrect-strict-equality)
        if (IERC20(token0).balanceOf(address(this)) - bal0Before != amount0) revert FeeOnTransferUnsupported();
        // forge-lint: disable-next-line(incorrect-strict-equality)
        if (IERC20(token1).balanceOf(address(this)) - bal1Before != amount1) revert FeeOnTransferUnsupported();

        uint256 _totalSupply = totalSupply;
        if (_totalSupply == 0) {
            shares = _sqrt(amount0 * amount1) - MINIMUM_LIQUIDITY;
            balanceOf[address(0)] = MINIMUM_LIQUIDITY;
            _totalSupply = MINIMUM_LIQUIDITY;
        } else {
            shares = _min((amount0 * _totalSupply) / bal0Before, (amount1 * _totalSupply) / bal1Before);
        }

        if (shares == 0) revert InsufficientLiquidityMinted();
        balanceOf[to] += shares;
        totalSupply = _totalSupply + shares;

        emit Deposited(to, amount0, amount1, shares, block.timestamp);
    }

    /**
     * @notice Withdraws underlying assets by burning shares.
     * @dev EXIT GUARANTEE: Never restricted by paused state. Users can ALWAYS withdraw.
     * @param shares Amount of shares to burn.
     * @param to Recipient of underlying assets.
     * @return amount0 Received amount of token0.
     * @return amount1 Received amount of token1.
     */
    function withdraw(uint256 shares, address to) external nonReentrant returns (uint256 amount0, uint256 amount1) {
        if (shares == 0) revert ZeroAmount();
        if (to == address(0)) revert ZeroAddress();
        if (balanceOf[msg.sender] < shares) revert InsufficientLiquidityBurned();

        uint256 total0 = IERC20(token0).balanceOf(address(this));
        uint256 total1 = IERC20(token1).balanceOf(address(this));
        uint256 _totalSupply = totalSupply;

        amount0 = (shares * total0) / _totalSupply;
        amount1 = (shares * total1) / _totalSupply;
        if (amount0 == 0 && amount1 == 0) revert InsufficientLiquidityBurned();

        balanceOf[msg.sender] -= shares;
        totalSupply = _totalSupply - shares;

        IERC20(token0).safeTransfer(to, amount0);
        IERC20(token1).safeTransfer(to, amount1);

        emit Withdrawn(msg.sender, shares, amount0, amount1, block.timestamp);
    }

    // ==========================================
    // REACTIVE CALLBACK EXECUTION ENTRYPOINT
    // ==========================================

    /**
     * @notice Reactive execution callback triggered exclusively by Reactive Network CallbackProxy.
     * @param sender Reactive contract that authorized the callback on Lasna.
     * @param payload ABI-encoded opportunity execution instructions.
     */
    function executeCallback(address sender, bytes calldata payload)
        external
        nonReentrant
        whenNotPaused
        onlyCallbackSender(sender)
    {
        // Dual authentication: Caller must be the authorized callback proxy
        if (msg.sender != address(_SERVICE_PROVIDER)) {
            revert UnauthorizedCallbackCaller(msg.sender);
        }

        (bytes32 opportunityId, bool isBuyToken0, uint256 amountIn, uint256 minAmountOut, uint256 deadline) =
            abi.decode(payload, (bytes32, bool, uint256, uint256, uint256));

        // Replay Protection
        if (executedOpportunities[opportunityId]) {
            revert OpportunityAlreadyExecuted(opportunityId);
        }
        executedOpportunities[opportunityId] = true;

        // Verification 1: Execution Deadline
        if (block.timestamp > deadline) {
            _recordFailure(opportunityId, "DEADLINE_EXPIRED");
            return;
        }

        // Verification 2: Maximum Trade Size Bound
        if (amountIn > maxTradeSize) {
            _recordFailure(opportunityId, "SIZE_EXCEEDS_MAX");
            return;
        }

        // Verification 3: Inventory Availability
        address inToken = isBuyToken0 ? token1 : token0;
        address outToken = isBuyToken0 ? token0 : token1;
        uint256 currentBal = IERC20(inToken).balanceOf(address(this));
        if (currentBal < amountIn) {
            _recordFailure(opportunityId, "INSUFFICIENT_INVENTORY");
            return;
        }

        // Verification 4: Real-time Pool Price & Slippage Check
        (uint112 r0, uint112 r1,) = pool.getReserves();
        (uint256 rIn, uint256 rOut) = isBuyToken0 ? (uint256(r1), uint256(r0)) : (uint256(r0), uint256(r1));

        uint256 expectedOut = pool.getAmountOut(amountIn, rIn, rOut);
        if (expectedOut < minAmountOut) {
            _recordFailure(opportunityId, "SLIPPAGE_EXCEEDED");
            return;
        }

        // Execute leg trade against local pool
        IERC20(inToken).safeTransfer(address(pool), amountIn);
        uint256 amount0Out = isBuyToken0 ? expectedOut : 0;
        uint256 amount1Out = isBuyToken0 ? 0 : expectedOut;

        uint256 balOutBefore = IERC20(outToken).balanceOf(address(this));
        pool.swap(amount0Out, amount1Out, address(this), new bytes(0));
        uint256 actualOut = IERC20(outToken).balanceOf(address(this)) - balOutBefore;

        if (actualOut < minAmountOut) {
            _recordFailure(opportunityId, "POST_SWAP_SLIPPAGE");
            return;
        }

        // Reset consecutive failures on successful execution
        consecutiveFailures = 0;
        emit LegExecuted(opportunityId, isBuyToken0, amountIn, actualOut, block.timestamp);
    }

    function _recordFailure(bytes32 opportunityId, string memory reason) internal {
        consecutiveFailures++;
        emit LegSkipped(opportunityId, reason, block.timestamp);

        // Circuit breaker: pause strategy after N consecutive failed / skipped legs
        if (consecutiveFailures >= maxConsecutiveFailures) {
            _pause();
            emit LegFailed(opportunityId, "CIRCUIT_BREAKER_TRIPPED", block.timestamp);
        }
    }

    // ==========================================
    // BOUNDED ADMIN PARAMETERS
    // ==========================================

    function setParameters(uint256 maxTradeSize_, uint256 maxSlippageBps_, uint256 maxConsecutiveFailures_)
        external
        onlyOwner
    {
        if (maxSlippageBps_ > ABSOLUTE_MAX_SLIPPAGE_BPS) revert ParameterOutOfBounds("maxSlippageBps");
        if (maxConsecutiveFailures_ == 0 || maxConsecutiveFailures_ > 50) {
            revert ParameterOutOfBounds("maxConsecutiveFailures");
        }
        if (maxTradeSize_ == 0) revert ParameterOutOfBounds("maxTradeSize");

        maxTradeSize = maxTradeSize_;
        maxSlippageBps = maxSlippageBps_;
        maxConsecutiveFailures = maxConsecutiveFailures_;

        emit ParametersUpdated(maxTradeSize_, maxSlippageBps_, maxConsecutiveFailures_);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        consecutiveFailures = 0;
        _unpause();
    }

    // ==========================================
    // MATH HELPERS
    // ==========================================

    function _sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function _min(uint256 x, uint256 y) internal pure returns (uint256) {
        return x < y ? x : y;
    }
}
