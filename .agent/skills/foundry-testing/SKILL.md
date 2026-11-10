---
name: foundry-testing
description: Standards, flags, and practices for Foundry testing, fuzzing, invariants, and fork testing.
---

# Foundry Testing Skill

## Testing Principles
- Unit tests for all pure math (basis point conversions, fee calculations, drift tracking).
- Fuzzing on price gap thresholds, fee subtractions, and slippage tolerances.
- Invariant tests for vault non-custodial solvency: `vaultBalance >= sum(userDeposits)`.
- Mocking the `ISystemContract` (`0x8888888888888888888888888888888888888888`) and callback proxy to test reactive logic in deterministic local environments.

## Keystore & Deployment Flags
- Keystore name: `deployer`
- Keystore password file: `~/.foundry/.halfway-pass`
- Command format:
  ```bash
  forge script script/Deploy.s.sol:DeployScript \
      --rpc-url <RPC_URL> \
      --account deployer \
      --password-file ~/.foundry/.halfway-pass \
      --broadcast \
      --verify
  ```
- Always check chain ID in scripts before broadcasting.
- Enforce spending limit checks before sending transactions.
