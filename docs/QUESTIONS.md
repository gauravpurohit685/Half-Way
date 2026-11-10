# Questions & Design Decisions

This document tracks questions, architectural alternatives, and user decisions resolved at project gates.

## Gate A Questions (Submitted for User Approval)

1. **Pair / DEX Selection Trade-off:**
   - **Option A (Existing Uniswap V3 WETH/USDC pools):**
     - Base Sepolia: `0x94bfc0574FF48E92cE43d495376C477B1d0EEeC0` (500 fee) / `0x46880b404CD35c165EDdefF7421019F8dD25F4Ad` (3000 fee).
     - Unichain Sepolia: `0xBeAD5792bB6C299AB11Eaa425aC3fE11ebA47b3B` (500 fee) / `0x8F463126bBEA80A10DF9Bf6FF5455B6B0292B34e` (3000 fee).
     - *Pros:* Real Uniswap V3 liquidity on both chains.
     - *Cons:* Disparate USDC faucet tokens; V3 concentrated liquidity math requires tick-to-price conversion in reactive contract; higher gas for test shocks.
   - **Option B (Dedicated Halfway Constant-Product Test Pools with Mock Tokens, e.g., HALF / WETH):**
     - Deploy standard Uniswap V2 / Constant-Product test pools on Base Sepolia and Unichain Sepolia funded with initial calibrated liquidity.
     - *Pros:* Deterministic price impact, simple swap events (`Sync(reserve0, reserve1)` / `Swap`), fast calibrated price shocks with minimal testnet ETH, zero external dependency on testnet USDC faucets.
   - **Recommendation:** Option B (or an adapter layer that supports Option B for rock-solid testnet demo loops while keeping the adapter interface compatible with V3).

2. **Proposed Default Inventory & Strategy Thresholds:**
   - **Vault Inventory:** 0.02 ETH + equivalent token inventory on each chain.
   - **Threshold:** 50 bps (0.50%) net of estimated fees.
   - **Max Trade Size per Loop:** 0.005 ETH per execution leg.
   - **Cooldown:** 5 seconds (timestamp-based) between automated executions for the same pair.

3. **Hosting Preference for Indexer & Frontend:**
   - Next.js frontend + Indexer (Ponder / fast polling indexer with SQLite).
   - Local production build + static/Vercel/Railway export readiness.
