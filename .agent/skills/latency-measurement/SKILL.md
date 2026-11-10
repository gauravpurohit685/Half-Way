---
name: latency-measurement
description: Protocols and methodologies for measuring hop-by-hop latency and gap decay half-life in Halfway.
---

# Latency Measurement Skill

## Hop Anatomy
Every cross-chain loop measures four distinct hops:
1. **Hop 1: Origin Swap (T0)**: Inclusion of the initial price-shocking swap on Pool A or B.
   - Captured: `block.timestamp` and block number on origin chain.
2. **Hop 2: Reactive Reaction (T1)**: Inclusion of the reactive reaction transaction on Reactive Lasna.
   - Captured: `block.timestamp` and tx hash on Lasna.
3. **Hop 3: Destination Callback Execution (T2)**: Inclusion of the callback trade transaction on the destination chain.
   - Captured: `block.timestamp` and tx hash on destination chain.
4. **Hop 4: Gap Closed (T3)**: The moment both pools' prices reconverge within user threshold.
   - Captured: Final pool state timestamp.

## Dual Timestamping
Because L2 block timestamps may have coarse granularity (e.g. 1s resolution despite 200ms block intervals), Halfway records:
- **On-chain Header Timestamps**: Formally provable, consensus-stamped.
- **Off-chain Observer Wall-Clock**: Millisecond-resolution reception time recorded by the indexer daemon.
Both are clearly labelled in the UI and exports.

## Metric Calculation
- **Reaction Latency**: $T_2 - T_0$ (Origin swap to destination callback execution).
- **Reactive Processing Time**: $T_1 - T_0$ (Origin event to Lasna reaction block).
- **Callback Relay Time**: $T_2 - T_1$ (Lasna callback request to destination confirmation).
- **Gap Half-Life**: Time taken for the initial price dislocation $(\Delta P_0)$ to halve:
  $$\tau_{1/2} = \frac{\ln(2)}{\lambda}$$
  fitted from post-shock price observations.
- **Loss Under Slower Latency**: Computed counterfactual profit erosion comparing actual execution time against simulated legacy latency (e.g. 7.0s baseline).
