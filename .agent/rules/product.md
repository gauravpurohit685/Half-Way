# Non-Negotiable Product Rules

1. **Zero Guesswork / No Assumed Values:**
   - Contract addresses, pool pairs, fee tiers, gas limits, and callback proxy endpoints must originate from verified official documentation, validated on-chain state, `.env`, or explicit user instructions.
   - Never inject placeholder or dummy addresses into production code.

2. **Schema-Validated Configuration:**
   - All environment variables, chain configs, and contract registries must be strictly typed and validated using `zod`. Missing or invalid configurations must fail loudly at startup.

3. **Real Data Integrity:**
   - Never invent or fabricate transactions, hashes, prices, execution latencies, or PnL numbers.
   - Empty states must explicitly display "no data yet" with actionable guidance on generating real on-chain activity.
   - Replay functionality must strictly replay REAL recorded historical runs and be explicitly labelled `REPLAY`.

4. **Measured vs. Simulated Distinction:**
   - Real metrics must state their provenance (block header timestamp vs. off-chain observer wall-clock).
   - Any counterfactual modeling (such as "what if latency were 7s") must be unmistakably badged as `SIMULATED`.

5. **Omni Architecture Compliance:**
   - Target Reactive Network Omni (Lasna chain ID 5318007, CometBFT ~1s instant finality).
   - Do NOT use legacy Reactive patterns:
     - No `vm` state variable or `if (!vm)` branching.
     - No dual deployment artifacts.
     - No `emit Callback(...)` for primary cross-chain messaging; invoke `SYSTEM.requestCallback(...)` / `SYSTEM.requestCallbackV_1_0(...)`.
     - Subscriptions must use `SYSTEM.subscribe(...)`.
     - Callbacks on destination chains must authenticate via `onlyCallbackSender(address)`.
     - Adhere strictly to `@reactive-lib-omni` base contracts and interfaces.

6. **Timestamps for Timing:**
   - Always use unix timestamps (`block.timestamp`), never block numbers, for cooldowns, deadlines, and latency tracking (L2 block times are sub-second e.g. Base Sepolia ~200ms).
