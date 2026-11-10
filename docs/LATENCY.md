# Latency Lab Benchmarks & Data

This document tracks all recorded cross-chain loop latencies, hop-by-hop timings, and gap half-life calculations.

## Hop Definitions
- **Hop 1 ($T_0$)**: Origin swap inclusion (Base Sepolia or Unichain Sepolia).
- **Hop 2 ($T_1$)**: Reactive reaction transaction inclusion on Reactive Lasna (Chain ID: 5318007).
- **Hop 3 ($T_2$)**: Destination callback execution inclusion on destination chain.
- **Hop 4 ($T_3$)**: Price gap reconvergence verified across pools.

## Benchmarks Table (Recorded Runs)
*Runs will be populated during Phase 1 (Hello-Loop) and Phase 5 (Recorded Runs).*

| Run ID | Origin Chain | Dest Chain | Origin Tx ($T_0$) | Lasna Tx ($T_1$) | Dest Tx ($T_2$) | Reaction Latency ($T_2 - T_0$) | Header $\Delta T$ | Observer $\Delta T$ | Gap Half-Life ($\tau_{1/2}$) | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| *Pending Gate A & Phase 1* | - | - | - | - | - | - | - | - | - | - |

## Counterfactual Loss Modeling (SIMULATED)
*Calculated comparison of capture volume and slippage between Omni (~1s reaction) versus legacy systems (~7s latency).*
