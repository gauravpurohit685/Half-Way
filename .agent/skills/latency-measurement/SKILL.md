---
name: latency-measurement
description: Protocols and methodologies for measuring hop-by-hop latency and gap decay half-life in Halfway.
---

# Latency Measurement Skill

## 1. Ground Rules & Honest Definitions
1. **No Organic Decay**: Our liquidity pools on Base Sepolia and Unichain Sepolia are isolated test pools with no external competing arbitrageurs. A price gap never decays on its own. We explicitly do **not** claim an organic "natural gap half-life".
2. **Measured vs Simulated**: All headline metrics ($T_0 \to T_1 \to T_2 \to T_3$, $T_{1/2}$, $T_{\text{close}}$) are strictly measured. Counterfactual loss comparisons are strictly labeled as a **SIMULATED** latency budget model.

## 2. Hop Anatomy
Every cross-chain loop measures four distinct hops:
1. **Hop 1: Origin Swap ($T_0$)**: Inclusion of the initial price-shocking swap on Pool A or B.
   - Captured: `block.timestamp`, block number, and synchronized observer `observedAt` in ms.
2. **Hop 2: Reactive Reaction ($T_1$)**: Inclusion of the reactive reaction transaction on Reactive Lasna.
   - Captured: `block.timestamp`, Lasna block number, tx hash, and observer `observedAt` in ms.
3. **Hop 3: Destination Callback Execution ($T_2$)**: Inclusion of the callback trade transaction on destination chain.
   - Captured: `block.timestamp`, destination block number, tx hash, and observer `observedAt` in ms.
4. **Hop 4: Gap Closed ($T_3$)**: The moment normalized price gap between both pools falls to or below threshold ($G \le \text{threshold}$).
   - Captured: Final pool state timestamp and observer `observedAt` in ms.

## 3. Measured Closure Metrics
- **Half-Closure Time ($T_{1/2}$ - Measured)**: Real elapsed time from shock swap inclusion ($T_0$) until the normalized price gap first falls to 50% of its initial post-shock magnitude ($G(t) \le 0.5 \cdot G_0$).
- **Total Closure Time ($T_{\text{close}}$ - Measured)**: Real elapsed time from $T_0$ until the gap is at or below threshold ($G(t) \le \text{threshold}$).

## 4. Competitive Latency Budget Model (SIMULATED)
$$\text{Remaining Opportunity Share} = \left(\frac{1}{2}\right)^{\frac{L}{h}}$$
Where $h$ is assumed competitor half-life (default: 5.0s), and $L$ is evaluated latency (e.g., measured p50 vs legacy 7.0s baseline). Always displayed with `[SIMULATION MODEL]` label.

## 5. Headline Aggregation Standards
- Only **COMPLETE** loops ($T_0 \to T_1 \to T_2 \to T_3$) are counted in aggregate headline statistics (p50, p90, max).
- Incomplete, skipped, or failed executions are logged with explicit reason codes (`DEADLINE_EXPIRED`, `SLIPPAGE_EXCEEDED`, `BELOW_HURDLE`, `RELAYER_PENDING`) and reported separately in exclusions breakdown.
- Dual-timestamp labeling: Every timestamp must be explicitly labeled as consensus block time or calibrated observer time.
