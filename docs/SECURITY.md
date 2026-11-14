# Security & Threat Model

**Project:** Halfway Cross-Chain Arbitrage Vault  
**Audit Target:** `HalfwayExecutor.sol`, `HalfwayReactive.sol`, `HalfPair.sol`, `MockERC20.sol`  

---

## 1. Threat Model & Mitigations

### 1.1 Stale Cross-Chain Data
- **Risk:** Price events from Chain A may take seconds to reach Reactive Lasna, and callbacks to Chain B take additional seconds. During network congestion, prices may have moved, causing arbitrage trades to execute at an unhedged loss.
- **Mitigation:**
  1. **Max Staleness Enforcement:** In `HalfwayReactive.sol`, if the peer pool price is older than `maxStalenessSeconds` (default: 60s), the opportunity is discarded.
  2. **Execution Deadline:** Every callback contains an on-chain timestamp deadline (`block.timestamp + executionTimeoutSeconds`). If expired, `HalfwayExecutor` aborts immediately with `LegSkipped(opportunityId, "DEADLINE_EXPIRED")`.
  3. **Local Re-Verification:** `HalfwayExecutor` reads real-time local pool reserves at callback arrival time. If the executed swap would yield less than `minAmountOut`, the trade aborts with `LegSkipped(opportunityId, "SLIPPAGE_EXCEEDED")`.

### 1.2 Price Manipulation & Front-running
- **Risk:** Flash loans or large local swaps could artificially dislocate pool prices to trigger vault trades that arbitrageurs extract value from.
- **Mitigation:**
  1. **Fee-Adjusted Hurdle:** Opportunities are evaluated strictly net of both pools' swap fees (30 bps + 30 bps = 60 bps) PLUS an extra safety margin (10 bps) PLUS user threshold (50 bps).
  2. **Bounded Trade Sizing:** Trade sizes are closed-form calculated to close a fraction of the spread and strictly capped by `maxTradeSize`.
  3. **Cooldown Window:** `cooldownSeconds` prevents repetitive execution against rapid artificial price oscillations.

### 1.3 Griefing & Replay Attacks
- **Risk:** Malicious actors replaying callback payloads or injecting fabricated callback calls to drain inventory.
- **Mitigation:**
  1. **Dual Authentication:** `HalfwayExecutor` verifies that `msg.sender == address(_SERVICE_PROVIDER)` (the official Reactive `CallbackProxy`) AND `onlyCallbackSender(sender)` validates that the payload originator matches the immutable `_CALLBACK_SENDER` (our Lasna contract).
  2. **Deterministic Replay Protection:** Every callback carries a unique `opportunityId` (`keccak256(timestamp, chainId, emitter, nonce)`). Re-execution of an existing `opportunityId` reverts with `OpportunityAlreadyExecuted`.

### 1.4 Partial Fills & Asymmetric Execution
- **Risk:** In an inventory-based cross-chain system, Leg A on Chain A may execute while Leg B on Chain B is skipped or fails due to network latency, creating unhedged token imbalance.
- **Mitigation:**
  1. **Detailed Event Logging:** Emits explicit `LegExecuted`, `LegSkipped`, and `LegFailed` events carrying `opportunityId`, reasons, and timestamps for indexer observability.
  2. **Circuit Breaker:** `consecutiveFailures` tracks failed or skipped legs. When failures reach `maxConsecutiveFailures` (default: 5), the executor automatically trips the circuit breaker and enters the `paused` state.

### 1.5 Admin Abuse & Fund Custody
- **Risk:** Malicious or compromised admin keys draining depositor funds or altering parameters maliciously.
- **Mitigation:**
  1. **Non-Custodial Design:** The owner has NO ability to sweep or withdraw user funds from `HalfwayExecutor`.
  2. **Exit Guarantee:** The `withdraw()` function is NOT gated by `whenNotPaused`. Depositors can ALWAYS withdraw their underlying assets, even if the strategy is paused.
  3. **Bounded Admin Parameters:** Admin setters strictly enforce hard bounds (e.g., `maxSlippageBps <= 500` [5.0%], `maxConsecutiveFailures <= 50`).
  4. **Two-Step Ownership:** Implements OpenZeppelin `Ownable2Step` to prevent accidental transfer of admin authority to invalid addresses.

---

## 2. Static Analysis & Linter Findings

### 2.1 Foundry Linter Checks
- **Strict Equality on Balances (`incorrect-strict-equality`):**
  - *Location:* `HalfwayExecutor.deposit()`
  - *Justification:* Intentionally used to verify `balanceAfter - balanceBefore == amount` to explicitly reject fee-on-transfer and rebasing tokens.
- **Reentrancy Protection (`reentrancy-no-eth` / `reentrancy-events`):**
  - *Location:* `HalfwayExecutor.executeCallback()`, `HalfPair.swap()`
  - *Justification:* Both contracts inherit OpenZeppelin `ReentrancyGuard` with all state updates preceding external token transfers following CEI patterns.
- **Timestamps (`block-timestamp`):**
  - *Location:* Cooldowns, deadlines, and latency logs.
  - *Justification:* On L2s and Lasna, block timestamps are the canonical measure of real-world latency (as opposed to block numbers, which vary widely between 200ms on Base and 1s on Lasna).

---

## 3. Slither Static Analysis Review

All contracts adhere to standard Slither safety best practices:
- Reentrancy protection on all value-moving entrypoints.
- SafeERC20 utilized for all token transfers.
- Explicit custom errors throughout, avoiding generic reverts.
- Zero-address checks in constructors and setters.
- Immutables used for all fixed dependencies.
