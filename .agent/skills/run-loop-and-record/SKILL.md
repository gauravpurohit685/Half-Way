---
name: run-loop-and-record
description: Automated workflow for executing alternating cross-chain price shock loops, restoring AMM equilibrium, and recording calibrated multi-hop latencies.
---

# /run-loop-and-record Workflow

This workflow automates live on-chain cross-chain arbitrage loops between Base Sepolia and Unichain Sepolia via Reactive Lasna.

## Operational Protocol

1. **Pre-flight Health & Spending Safeguards**:
   - Queries deployer native balances across all 3 chains:
     - Base Sepolia: Must be $\ge 0.03\text{ ETH}$.
     - Unichain Sepolia: Must be $\ge 0.03\text{ ETH}$.
     - Reactive Lasna: Must be $\ge 10.0\text{ lREACT}$.
   - Spending per execution leg must remain $\le 0.02\text{ ETH}$ or $\le 5.0\text{ lREACT}$.
   - If balances approach the floor, execution aborts immediately.

2. **NTP Clock Calibration**:
   - Measures local WSL2 clock drift against Cloudflare/Google trusted HTTP time endpoints.
   - Calculates and persists `CLOCK_OFFSET` in milliseconds.
   - Applies offset to every wall-clock observation (`observedAt = time.time() + offset`).

3. **Alternating Price Shock Direction**:
   - **Odd Runs**: Shock applied to Base Sepolia (Token0 $\to$ Token1 swap of 4.0 ETH).
   - **Even Runs**: Shock applied to Unichain Sepolia (Token1 $\to$ Token0 swap of 4.5 ETH).

4. **Multi-Hop Event & Timing Capture**:
   - **$T_0$ (Origin Swap)**: Records transaction hash, block number, consensus `block.timestamp`, and calibrated `observedAt` in ms.
   - **$T_1$ (Reactive Processing)**: Polls Lasna for `totalOpportunitiesDetected()` increment; records Lasna reaction tx hash, block number, block time, and `observedAt` in ms.
   - **$T_2$ (Callback Execution)**: Detects callback inclusion on destination chain executor; records tx hash, block number, block time, and `observedAt` in ms.
   - **$T_3$ (Gap Convergence)**: Re-evaluates post-trade normalized price gap between both pools; logs $T_{1/2}$ and $T_{\text{close}}$.

5. **Equilibrium Rebalancing**:
   - After each loop, reads reserves $(r_0, r_1)$ on the shocked pool.
   - If reserves deviate from 1:1 parity ($|r_0 - r_1| > 0.2\text{ ETH}$), executes a corrective swap using mintable test tokens to reset both pools to ~100:100.
   - Prevents inventory drift and guarantees identical starting liquidity for subsequent runs.

6. **Raw Data Persistence**:
   - Appends complete JSON records to `data/runs/run_{YYYYMMDD}.jsonl`.
   - Never logs private keys, passwords, or RPC URLs with embedded tokens.
