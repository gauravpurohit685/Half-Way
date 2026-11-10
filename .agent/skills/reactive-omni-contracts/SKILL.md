---
name: reactive-omni-contracts
description: Guide and patterns for developing Reactive Smart Contracts on Reactive Network Omni architecture.
---

# Reactive Omni Contracts Skill

## Architecture Overview
Reactive Network Omni uses CometBFT consensus with ~1.0s block times and instant finality. Contracts live on Reactive Lasna (Chain ID: `5318007`).

## Core Conventions
- **Base Contract**: Inherit from `AbstractReactive` in `@reactive-lib-omni`.
- **System Contract**: Precompile / system contract located at `0x8888888888888888888888888888888888888888`.
- **Subscriptions**: In constructor or initialization:
  ```solidity
  SYSTEM.subscribe(
      originChainId,
      originContractAddress,
      topic0,
      topic1,
      topic2,
      topic3
  );
  ```
- **Reaction Entrypoint**:
  ```solidity
  function react(LogRecord calldata log_) external onlySystem {
      // Process log
  }
  ```
- **Callbacks**:
  Use `SYSTEM.requestCallbackV_1_0(config)` instead of deprecated `emit Callback`:
  ```solidity
  ISystemContract.CallbackConfiguration_V_1_0 memory config = ISystemContract.CallbackConfiguration_V_1_0({
      chainId: destinationChainId,
      recipient: destinationExecutorAddress,
      gasLimit: gasLimit,
      payload: abi.encodeWithSignature("executeCallback(address,...)", address(this), ...)
  });
  SYSTEM.requestCallbackV_1_0(config);
  ```
- **Destination Callbacks**:
  Contracts receiving callbacks inherit `AbstractCallback(callbackProxy, reactiveContractAddress)`.
  Authentication uses modifier `onlyCallbackSender(callbackSender)`.
- **Debt & Funding**:
  Reactive contracts must maintain sufficient lREACT balance to cover reactive execution fees. Call `_coverDebt()` or maintain native balance.
