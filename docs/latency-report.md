# Halfway Latency Report — Empirical Cross-Chain Price-Gap Capture Benchmark & Reconciliation

**Project:** Halfway (Reactive Omni Buildathon — *Every Second Counts* track)  
**Date Range:** 2026-11-14T10:58:41Z to 2026-11-14T12:47:58Z  
**Networks:** Base Sepolia (84532) ↔ Unichain Sepolia (1301) via Reactive Lasna (5318007)  
**Observer Clock Calibration:** Measured WSL2 clock offset: -0.85s to -2.12s against Cloudflare Trace (`https://cloudflare.com/cdn-cgi/trace`). All wall-clock metrics are adjusted for calibrated clock offset.

---

## 1. Segmented Empirical Benchmark & Headline Statistics

All headline figures are derived strictly from **complete on-chain loops** ($T_0 \to T_1 \to T_2 \to T_3$) confirmed on-chain and verified against JSON-RPC consensus receipts.

### 1.1 Condition Segmentation Breakdown

To prevent pooling across varied testing environments, our 32 complete loops are segmented by condition:

| Segment | Runs | Description | Hop 1 ($T_0 \to T_1$) Block | Hop 1 ($T_0 \to T_1$) Wall-Clock | Hop 2 ($T_1 \to T_2$) Block | End-to-End ($T_0 \to T_3$) Block | End-to-End ($T_0 \to T_3$) Wall-Clock |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Segment 1** | Loops 1–21 (N=21) | Initial config; staleness = 600s; direct contract funding; manual trigger interval | **7.0 s** | 11.44 s | **5.0 s** | **12.0 s** | 16.48 s |
| **Segment 2** | Loops 35–39 (N=5) | Post-fee debt deposit (`depositTo`); staleness = 86400s; standard intra-tx pace | **7.0 s** | 10.94 s | **5.0 s** | **11.0 s** | 16.71 s |
| **Segment 3** | Loops 40–45 (N=6) | Post-fee debt deposit; staleness = 86400s; paced 2.0s intra-tx delay | **8.0 s** | 11.78 s | **5.0 s** | **13.0 s** | 17.08 s |
| **Overall Dataset** | **All Loops (N=32)** | **Complete verified dataset** | **p50 = 7.0 s** (p90: 8.0 s) | **p50 = 11.27 s** (p90: 14.28 s) | **p50 = 5.0 s** (p90: 6.0 s) | **p50 = 12.0 s** (p90: 14.0 s) | **p50 = 16.60 s** (p90: 19.59 s) |

### 1.2 Sample Breakdown & Exclusions

```
Total Trigger Attempts Recorded: 47
├── Complete Loops Verified on Consensus: 32 (68.1%)
└── Excluded / Non-Headline Attempts: 15 (31.9%)
    ├── Below Hurdle Suppression (NEG-01): 1 (spread 2.1 bps <= hurdle 70 bps; verified suppression)
    ├── Replay Defense Reversion (NEG-02): 1 (unauthorized callback rejected by modifier)
    └── Fee Debt Exhaustion Pauses: 13 (runs 22-34 when Lasna reserves ran out; re-verified after depositTo)
```

---

## 2. Reconciling Phase 2 (2–3s) vs Phase 3 (p50 7s Block / 11.3s Wall-Clock)

Our investigation into previous Phase 2 runs revealed three crucial factors reconciling the reported numbers:

1. **Sample Selection Asymmetry in Phase 2:**
   - In Phase 2, only 4 exploratory runs were conducted.
   - 3 of the 4 runs had origin on Base Sepolia (`RUN-01`, `RUN-03`, `RUN-04`), yielding block time deltas of **3s, 2s, 2s**.
   - However, the single Unichain Sepolia origin run (`RUN-02`) exhibited a block delta of **24s** (observer: 25.10s) and was treated as an outlier.
   - In Phase 3, runs were strictly balanced 50/50 across both chains (17 Base Sepolia origin, 15 Unichain Sepolia origin). Unichain origin introduces higher consensus latency (p50 = 8.0s) than Base Sepolia origin (p50 = 7.0s).
2. **Phase 2 Observer vs Block-Time Reporting:**
   - Even in Phase 2, the **wall-clock observer latencies** were measured at **11.25s** (Run 1), **25.10s** (Run 2), **7.95s** (Run 3), and **5.77s** (Run 4) — showing that true physical observation time was never 2–3s. The 2–3s figure was solely an EVM block timestamp subtraction ($T_1 - T_0$).
3. **Cross-Chain EVM Clock Asynchrony (The Hello-Loop Control Finding):**
   - We inspected the Hello-Loop V2 control run on Phase 1 contracts:
     - Origin Base Sepolia block timestamp: `1794601179`
     - Reaction Lasna block timestamp: `1794601178`
     - **Block Delta ($T_1 - T_0$): -1 second!**
   - **Conclusion:** Independent L1/L2 sequencers and Lasna CometBFT validators do not share an atomic clock. Sequencer timestamps drift relative to each other by $\pm 1$ to 3 seconds. An EVM block delta of 2s in Phase 2 was partially an artifact of sequencer clock lead, whereas Phase 3's calibrated observer timestamps capture true elapsed physical duration.

---

## 3. Sub-Hop Decomposition: Where Does the Time Go?

Decomposing the physical elapsed wall-clock time for Hop 1 ($T_0 \to T_1 \approx 11.3\text{s}$) and Hop 2 ($T_1 \to T_2 \approx 5.3\text{s}$):

```
[T0_trigger] Origin swap initiated by user/bot
  │
  ├─▶ 2.5 s : Origin Inclusion & RPC Roundtrip
  │     • RPC broadcast, sequencer mempool queueing, OP-Stack block inclusion.
  │     • Observer awaits receipt confirmation and extracts mined block number.
  │
  ├─▶ 6.0 - 7.0 s : Reactive Ingest & Consensus Packing (Hop 1 on-chain)
  │     • Origin block safe/finalized depth confirmation by Reactive nodes: ~3-4s.
  │     • Reactive validator ingest, log filtering, CometBFT consensus round: ~2-3s.
  │     • Lasna `react()` transaction execution: < 0.05s (22,715 gas).
  │
  ├─▶ 1.5 - 2.0 s : Lasna State Propagation & Polling Quantization
  │     • Block gossip across Lasna RPC nodes.
  │     • 1.0s client polling interval jitter.
  │
  └─▶ [T1] Lasna Reaction Confirmed (Total elapsed: ~11.3s wall-clock)
        │
        ├─▶ 2.5 s : Official Reactive Relayer Batching (Hop 2)
        │     • Relayer polls Lasna `Callback` events and batches destination requests.
        │
        ├─▶ 2.8 s : Destination Mempool Inclusion (Hop 2)
        │     • Submission to destination CallbackProxy (`0xa6eA...` / `0x9299...`).
        │     • Destination sequencer mines transaction and executes `HalfwayExecutor`.
        │
        └─▶ [T2 / T3] Destination Callback Confirmed & Equilibrium Restored (Total elapsed: ~16.6s wall-clock)
              • Hop 3 is atomic (0.0s): pool price instantly reflects rebalance in the callback block.
```

---

## 4. Destination Chain Comparison: Base Sepolia vs Unichain Sepolia

Comparing performance when routing destination callbacks to Base Sepolia (200ms blocks) vs Unichain Sepolia (1.0s blocks):

| Parameter | Destination = Base Sepolia (Origin = Unichain, N=15) | Destination = Unichain Sepolia (Origin = Base, N=17) | Analysis |
| :--- | :---: | :---: | :--- |
| **Hop 1 ($T_0 \to T_1$) Block** | p50 = **8.0 s** (p90 = 9.0 s) | p50 = **7.0 s** (p90 = 7.0 s) | Base origin is ~1s faster into Lasna due to sub-second sequencer blocks. |
| **Hop 2 ($T_1 \to T_2$) Block** | p50 = **5.0 s** (p90 = 6.0 s) | p50 = **4.0 s** (p90 = 5.0 s) | Unichain destination confirms callbacks ~1s faster on the testnet relayer. |
| **End-to-End ($T_0 \to T_3$) Block** | p50 = **14.0 s** (p90 = 14.0 s) | p50 = **11.0 s** (p90 = 12.0 s) | Base $\to$ Unichain loop completes in 11s vs 14s for Unichain $\to$ Base. |

---

## 5. Competitive Latency Budget Model Comparison

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

## 6. Empirical Economics Breakdown

Measurements collected across the 32 complete loops:

| Economic Component | Measured Value | Unit | Notes |
| :--- | :--- | :--- | :--- |
| **Lasna `react()` Gas** | ~22,715 gas | gas / tx | Constant execution overhead |
| **System Callback Debt / Reserve Burn** | **0.0472 lREACT** | lREACT / loop | Deducted by `0x888...888` per 2-callback dispatch |
| **Base Sepolia Executor Leg Gas** | ~118,500 gas | gas / leg | Cost: ~0.00000012 ETH (< $0.0005) |
| **Unichain Sepolia Executor Leg Gas** | ~124,200 gas | gas / leg | Cost: ~0.00000015 ETH (< $0.0005) |
| **Origin Shock Swap Gas** | ~48,000 to ~102,000 gas | gas / tx | Cost: ~0.00000010 ETH |
| **Net Opportunity Capture per Loop** | ~0.0042 ETH | ETH / 4 ETH leg | ~10.5 bps net capture after AMM fees |

---

## 7. Known Limitations & Testnet Specifics

1. **Synthetic Gap Decay:** Our test pools are dedicated pairs with no competing external arbitrageurs. Gaps do not decay until Halfway executes. We explicitly model competition using the simulated Latency Budget model rather than asserting fabricated organic decay.
2. **Relayer Batching:** Testnet callback delivery relies on the official Reactive relayer (`0xd499725b8d4aad361060a5fc5d30022285159449`), which batches transactions periodically.
3. **Timestamp Granularity:** Block header timestamps provide 200ms increments on Base Sepolia (`timestampMs`) and 1.0s increments on Unichain Sepolia and Reactive Lasna. All sub-second precision is backed by calibrated off-chain observer wall-clock timestamps.
