# /run-loop-and-record Workflow

## Purpose
Execute an end-to-end price-gap test shock, intercept reactive execution, trigger callbacks, measure hop-by-hop latency, and write a verifiable execution report.

## Steps
1. Query baseline prices and pool ticks on Base Sepolia and Unichain Sepolia.
2. Execute a calibrated swap transaction on the designated origin pool (e.g., Base Sepolia) using the test user or deployer account to create a controlled price dislocation.
3. Record Origin Tx Hash ($T_0$) and block timestamp.
4. Monitor Reactive Lasna for reaction transaction from `SYSTEM` to `HalfLifeReactive`. Record Lasna Tx Hash ($T_1$) and block timestamp.
5. Monitor Destination Chain for incoming callback from the proxy to `HalfLifeExecutor`. Record Destination Tx Hash ($T_2$) and block timestamp.
6. Verify price reconvergence on both pools ($T_3$).
7. Calculate hop-by-hop latencies:
   - Origin -> Reactive: $T_1 - T_0$
   - Reactive -> Callback: $T_2 - T_1$
   - Total Loop Latency: $T_2 - T_0$
8. Append full run data to `docs/LATENCY.md` and log actions in `docs/AGENT_LOG.md`.
