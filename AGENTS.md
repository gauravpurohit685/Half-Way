# Halfway Agent System Guidelines

This repository follows strict development guidelines for the **Halfway** cross-chain price-gap capture vault for the Reactive Omni Buildathon.

## Core Directives
1. **Safety First**: Testnets only (Sepolia, Base Sepolia, Unichain Sepolia, Reactive Lasna). Keep minimum wallet balances (0.03 ETH per L2, 10 lREACT on Lasna).
2. **Audit Logging**: Every on-chain transaction must be logged to `docs/AGENT_LOG.md`.
3. **Omni Architecture**: Built exclusively on Reactive Omni (`SYSTEM.subscribe`, `SYSTEM.requestCallbackV_1_0`, `onlyCallbackSender`). Legacy patterns (`vm`, `emit Callback`) are strictly forbidden.
4. **Honest Data**: No fabricated data. Empty states state "no data yet". Counterfactuals are badged `SIMULATED`.
5. **Rules & Conventions**:
   - Safety rules: `.agent/rules/safety.md`
   - Product rules: `.agent/rules/product.md`
   - Specification: `docs/SPEC.md`
   - Latency tracking: `docs/LATENCY.md`
   - Verified facts: `docs/VERIFIED_FACTS.md`
