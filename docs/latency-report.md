# Halfway Latency Report — Empirical Cross-Chain Price-Gap Capture Benchmark

**Project:** Halfway (Reactive Omni Buildathon — *Every Second Counts* track)  
**Date Range:** 2026-11-14T10:58:41Z to 2026-11-14T12:47:58Z  
**Networks:** Base Sepolia (84532) ↔ Unichain Sepolia (1301) via Reactive Lasna (5318007)  
**Observer Clock Calibration:** Measured WSL2 clock offset: -0.85s to -2.12s against Cloudflare Trace (`https://cloudflare.com/cdn-cgi/trace`). All wall-clock metrics are adjusted for calibrated clock offset.

---

## 1. Headline Statistics

All headline latency figures are computed **strictly from complete on-chain loops** ($T_0 \to T_1 \to T_2 \to T_3$) where every transaction was confirmed on-chain and cross-chain gap was closed.

| Metric | Sample Size | p50 (Block Time) | p90 (Block Time) | Max (Block Time) | p50 (Observer Wall-Clock) | p90 (Observer Wall-Clock) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hop 1 ($T_0 \to T_1$): Origin to Lasna** | 32 runs | **7.0 s** | 8.0 s | 11.0 s | **11,272 ms** | 14,281 ms |
| **Hop 2 ($T_1 \to T_2$): Lasna to Destination Callback** | 32 runs | **5.0 s** | 6.0 s | 6.0 s | **5,324 ms** | 6,502 ms |
| **Hop 3 ($T_2 \to T_3$): Destination to Equilibrium** | 32 runs | **0.0 s** | 0.0 s | 0.0 s | **0 ms** | 0 ms |
| **End-to-End ($T_0 \to T_3$)** | 32 runs | **12.0 s** | 14.0 s | 16.0 s | **16,598 ms** | 19,594 ms |
| **Half-Closure Time ($T_{1/2}$)** | 32 runs | **7.0 s** | 8.0 s | 11.0 s | — | — |
| **Total Closure Time ($T_{\text{close}}$)** | 32 runs | **12.0 s** | 14.0 s | 16.0 s | — | — |

### Sample Breakdown & Exclusions

```
Total Trigger Attempts Recorded: 47
├── Complete Loops Verified on Consensus: 32 (68.1%)
└── Excluded / Non-Headline Attempts: 15 (31.9%)
    ├── Below Hurdle Suppression (NEG-01): 1 (spread 2.1 bps <= hurdle 70 bps; verified suppression)
    ├── Replay Defense Reversion (NEG-02): 1 (unauthorized callback rejected by modifier)
    └── Fee Debt Exhaustion Pauses: 13 (runs 22-34 when Lasna reserves ran out; re-verified after depositTo)
```

---

## 2. Competitive Latency Budget Model Comparison

> [!NOTE]
> Our testnet pools have no external noise or competing arbitrage bots; hence, real gaps on testnet remain until Halfway trades them. The numbers below reflect our formal mathematical model:
> $$\text{Retained Opportunity Share} = \left(\frac{1}{2}\right)^{L / h}$$
> where $L$ is Halfway's measured empirical latency ($p50 = 12.0\text{s}$) and $h$ is an assumed competitor half-life.

| Assumed Competitor Half-Life ($h$) | Empirical Latency ($L = p50$) | Theoretical Retained Share | Theoretical Opportunity Loss | Competitive Assessment |
| :---: | :---: | :---: | :---: | :--- |
| **2.0 s** (Aggressive CEX/DEX arbitrageurs) | 12.0 s | **1.56%** | 98.44% | Highly vulnerable; requires direct Lasna RPC priority |
| **5.0 s** (Cross-rollup intent bridges) | 12.0 s | **18.95%** | 81.05% | Captures ~19% of theoretical peak volume |
| **7.0 s** (Standard L2 relayer networks) | 12.0 s | **30.48%** | 69.52% | Retains ~30% against standard cross-chain solvers |
| **12.0 s** (Equal latency threshold) | 12.0 s | **50.00%** | 50.00% | Exactly Halfway: captures 50% of price dislocation |
| **20.0 s** (Slow manual / batching rebalancers) | 12.0 s | **65.98%** | 34.02% | Dominates slower multi-block rebalancers |

---

## 3. Empirical Economics Breakdown

Measurements collected over the 32 complete loops:

| Economic Component | Measured Value | Unit | Notes |
| :--- | :--- | :--- | :--- |
| **Lasna `react()` Gas** | ~22,715 gas | gas / tx | Constant execution overhead |
| **System Callback Debt / Reserve Burn** | **0.0472 lREACT** | lREACT / loop | Deducted by `0x888...888` per 2-callback dispatch |
| **Base Sepolia Executor Leg Gas** | ~118,500 gas | gas / leg | Cost: ~0.00000012 ETH (< $0.0005) |
| **Unichain Sepolia Executor Leg Gas** | ~124,200 gas | gas / leg | Cost: ~0.00000015 ETH (< $0.0005) |
| **Origin Shock Swap Gas** | ~48,000 to ~102,000 gas | gas / tx | Cost: ~0.00000010 ETH |
| **Net Opportunity Capture per Loop** | ~0.0042 ETH | ETH / 4 ETH leg | ~10.5 bps net capture after AMM fees |

---

## 4. Narrative: Where Does the Time Go?

Breaking down the median 12.0s end-to-end loop:

```
[T0] Origin Swap Inclusion (Base Sepolia / Unichain Sepolia)
  │
  ├─▶ 7.0 seconds (58.3% of total time): Hop 1 (Origin Block → Lasna Event Ingestion & Reaction)
  │     • Origin block finality/safe propagation: ~2-3s
  │     • Reactive Network event ingest & CometBFT block packing: ~3-4s
  │     • Lasna `react()` evaluation and callback request dispatch: < 1s
  │
  ├─▶ 5.0 seconds (41.7% of total time): Hop 2 (Lasna Callback Request → Destination Inclusion)
  │     • Official Testnet Relayer batch polling: ~2-3s
  │     • Destination OP-Stack mempool inclusion and block commit: ~2-3s
  │
  └─▶ 0.0 seconds (0.0% of total time): Hop 3 (Callback Execution to Gap Closure)
        • The callback transaction atomically swaps against `HalfPair` and verifies invariant.
        • In the exact block where the callback is included, the pool price adjusts immediately.
```

### Bottleneck Analysis
1. **The Ingest & Ingestion Finality Pipeline:** The single largest component is the 7s delay between origin block inclusion and Lasna transaction confirmation. This is dominated by cross-chain RPC log polling and consensus confirmation on the origin L2 before the Reactive validators process the log record.
2. **Relayer Batch Interval:** The second largest component is the official testnet relayer batching delay (~5s). On production mainnet, specialized relayer infrastructure can reduce this to sub-2-second dispatch.

---

## 5. Known Limitations & Testnet Specifics

1. **Synthetic Gap Decay:** Our test pools are dedicated pairs with no competing external arbitrageurs. Gaps do not decay until Halfway executes. We explicitly model competition using the simulated Latency Budget model rather than asserting fabricated organic decay.
2. **Relayer Batching:** Testnet callback delivery relies on the official Reactive relayer (`0xd499725b8d4aad361060a5fc5d30022285159449`), which batches transactions periodically.
3. **Timestamp Granularity:** Block header timestamps provide 200ms increments on Base Sepolia (`timestampMs`) and 1.0s increments on Unichain Sepolia and Reactive Lasna. All sub-second precision is backed by calibrated off-chain observer wall-clock timestamps.
