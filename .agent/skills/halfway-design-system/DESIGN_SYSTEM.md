# Halfway Design System: "Isotope Lab"

## 1. Aesthetic Philosophy & Directives

Halfway is designed as a **precision nuclear physics instrument and laboratory field notebook**, measuring the rapid decay and capture of cross-chain price dislocation.

```
       ┌────────────────────────────────────────────────────────┐
       │   HALFWAY ISOTOPE LAB — PRECISION GAP SPECTROMETER    │
       │   Instrument Serif  •  Schibsted Grotesk  •  JetBrains │
       └────────────────────────────────────────────────────────┘
```

### Strict Banned Patterns
- **NO** blue-black, midnight, or purple neon gradients.
- **NO** glassmorphism, blurry cards, or glowing drop-shadow borders.
- **NO** stock 3D coins, rocket emojis, or generic crypto cliches.
- **NO** centered "hero + 3 KPI cards" marketing layouts.
- **NO** Inter or Roboto typography.
- **NO** unformatted numbers; every metric must use monospace tabular figures.

---

## 2. Design Tokens

### 2.1 Color Palette

| Token Name | Light Mode (Primary / Default) | Dark Mode (Warm Charcoal) | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| `--surface-paper` | `#EFEAE0` (Warm Bone) | `#14110E` (Deep Charcoal) | Canvas background; resembles heavyweight cotton rag paper. |
| `--surface-panel` | `#E5DFC9` (Aged Vellum) | `#1C1814` (Soft Charcoal) | Instrument panel container background. |
| `--surface-subtle` | `#DCD5BF` | `#241F1A` | Secondary container fill, card wells, code blocks. |
| `--text-ink` | `#15130F` (Carbon Black) | `#EFEAE0` (Bone White) | Primary text, titles, heavy metrics. High contrast (WCAG AAA). |
| `--text-graphite` | `#5B5750` (Graphite) | `#A39E93` (Muted Warm Gray) | Secondary labels, captions, metadata, unit descriptors. |
| `--border-hairline` | `#CFC8B8` (Paper Rule) | `#2A2620` (Dark Hairline) | 1px precision division lines, table rules, graticules. |
| `--signal-vermilion` | `#FF4B1F` (Signal Red-Orange) | `#FF4B1F` (Unchanged) | Open price gap, dislocated pool state, test shock trigger, warning. |
| `--reaction-lime` | `#C9F23A` (Scintillation Lime) | `#C9F23A` (Unchanged) | Closed gap, captured arbitrage, successful execution, verified loop. |
| `--signal-amber` | `#E59500` (Laboratory Amber) | `#E59500` (Unchanged) | Pending callback, low lREACT reserve fuel warning, cooldown state. |

### 2.2 Typography

Typography is self-hosted with zero external Google Fonts requests:

| Role | Font Family | Weights | Intended Use |
| :--- | :--- | :--- | :--- |
| **Headline & Display** | `Instrument Serif` | Regular (400), Italic (400) | Major titles, section headings, isotope labels, hero quotes. Italicized for emphasis. |
| **Interface & Prose** | `Schibsted Grotesk` | Regular (400), Medium (500), SemiBold (600) | Field labels, navigation, explanations, instructions, table headers. |
| **Numerals & Code** | `JetBrains Mono` | Regular (400), Bold (700) | Timestamps, bps, addresses, hashes, tabular metrics (`tabular-nums`). |

### 2.3 Spacing & Layout Grid
- **Base Grid:** Strict 4px scale: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`.
- **Chart Graticule:** 20px minor grid, 80px major grid printed in `--border-hairline` with subtle tick marks.
- **Instrument Panel Layout:** 3-column asymmetric layout on desktop (Strategy: 300px | Scope & Waterfall: 1fr | Ledger Tape: 320px). Collapses to single column with sticky action bar on mobile (< 768px).

### 2.4 Motion & Transitions
- Micro-interactions (hover, click): `150ms cubic-bezier(0.16, 1, 0.3, 1)`
- Panel expansion / tab switch: `250ms ease-out`
- Decay Scope trace: Vector path stroke-dashoffset animation over `600ms`. When a loop completes, the trace flashes `--reaction-lime` once (`400ms`), then settles.
- Reduced Motion: When `prefers-reduced-motion: reduce` is detected, animations are replaced with instantaneous state changes.

---

## 3. Core Components

### 3.1 `SourceBadge`
Every metric and number in Halfway carries a clear provenance badge:
- `[BLOCK]`: Solid graphite background, bone text. EVM block header timestamp (`timestampMs` on Base, block `timestamp` on Unichain/Lasna).
- `[OBSERVER]`: Ink background, bone text. NTP-calibrated off-chain wall-clock measurement in milliseconds.
- `[SIMULATION]`: Vermilion outline badge with dashed border. Explicitly counterfactual model.
- `[REPLAY]`: Graphite dashed outline badge. Real historical run replayed from archive.

### 3.2 `DecayScope` (Hero Instrument)
- Visual styling: Rectangular oscilloscope screen with millimeter-paper graticule background (`--surface-subtle` with `#CFC8B8` grid lines).
- Data trace: Normalized cross-chain price gap in basis points ($y$-axis) plotted against elapsed seconds ($x$-axis).
- Annotations:
  - Vertical crosshair at $T_0$ (Origin Shock).
  - Vertical crosshair at $T_1$ (Lasna Opportunity Detection).
  - Vertical crosshair at $T_2 / T_3$ (Destination Leg Executed & Gap Closed).
  - Horizontal marker at $Hurdle$ (Fee floor: 70 bps).
  - Big prominent numeric readout: **$T_{1/2} = 7.0\text{s}$** (half-closure time) and **$T_{\text{close}} = 12.0\text{s}$**.

### 3.3 `LoopAnatomy` (Ticker-Tape Waterfall)
- Stepped waterfall diagram showing each discrete hop:
  1. **Hop 0: Shock Inclusion** (`Origin Chain` → Tx hash, block number, $T_0$ time).
  2. **Hop 1: Reactive Ingestion** (`Reactive Lasna` → Tx hash, block number, $T_1$ time, delta $\Delta T_1$).
  3. **Hop 2: Callback Relayer** (`Destination Chain` → CallbackProxy tx hash, block number, $T_2$ time, delta $\Delta T_2$).
  4. **Hop 3: Equilibrium Settlement** (Atomic execution, price converged, delta $0.0\text{s}$).
- Clicking any hop opens an inline inspection drawer revealing transaction hashes, consensus receipt details, and block explorer links.

### 3.4 `IsotopeTile` (Periodic-Table Pool Block)
- Left element block: Base Sepolia (`Ba`, atomic number `84532`, 200ms blocks).
- Right element block: Unichain Sepolia (`Uni`, atomic number `1301`, 1.0s blocks).
- Center bridge: Live spread in basis points with dynamic arrow indicating direction of dislocation.

### 3.5 `LatencyBudgetSimulator`
- Interactive simulator allowing judges to test competitive scenarios:
  - Input slider: Reactive latency $L$ (default: measured p50 = 12.0s).
  - Input field: Assumed competitor half-life $h$ (default: 5.0s).
  - Formula display: $\text{Share} = 0.5^{L/h}$.
  - Realtime visualization: Retained opportunity bar vs theoretical loss bar.
  - One-click presets: *Measured p50 (12s)*, *Legacy Spec (7s)*, *Aggressive HFT (2s)*.

### 3.6 `FuelGauge`
- Shows Reactive Lasna system reserves and debt for `HalfwayReactive`:
  - `Reserves: 0.984 lREACT` (safe fuel bar in reaction lime).
  - `Debt: 0.000 lREACT`.
  - Warning banner when reserves drop below 0.20 lREACT.

### 3.7 `LedgerTape`
- Monospace receipt ticker styled like a continuous till receipt with perforated header and footer.
- Lists newest executed runs on top with Run ID, timestamp, initial gap, final gap, and status badge.

---

## 4. Static Mockup Layouts (3 Key Screens)

### 4.1 Screen 1: Console (`/`) — Instrument Panel

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ HALFWAY // ISOTOPE LAB              [0x0cDf...3953] [Base Sepolia / Unichain]  [Light/Dark] [● Live SSE] │
├───────────────────────────────┬────────────────────────────────────────┬───────────────────────────────┤
│ STRATEGY & VAULT INVENTORY    │ DECAY SCOPE (OSCILLOSCOPE)              │ LEDGER TAPE (MONOSPACE)       │
│                               │                                        │                               │
│ [Pair: mHALF / mWETH]         │ ┌────────────────────────────────────┐ │ ┌───────────────────────────┐ │
│ Base Pool:   102.68 / 102.67  │ │  GAP (bps)                         │ │ │ --- RECEIPT TAPE #45 ---  │ │
│ Uni Pool:    100.32 / 100.33  │ │ 800│   *                           │ │ │ 12:46:40 UTC  [EXECUTED]  │ │
│ Current Gap: 0.0 bps [NORMAL] │ │ 600│    \                          │ │ │ Orig: Base Sepolia Blk 586│ │
│                               │ │ 400│     \                         │ │ │ Lasna: Blk 8327822 (6s)   │ │
│ Vault Shares: 0.0000 mHV      │ │ 200│      *                        │ │ │ Dest: Uni Sepolia (10s)   │ │
│ [Deposit]  [Withdraw]         │ │   0└───*─────────────────────────  │ │ │ Initial Gap: 829.2 bps   │ │
│                               │ │    T0(0s) T1(6s)    T2/3(10s)      │ │ │ Final Gap:   0.0 bps     │ │
│ [FIRE TEST SHOCK] (4.0 ETH)   │ └────────────────────────────────────┘ │ │ PnL: +0.0042 ETH          │ │
│ Creates instant 830 bps gap   │  T½ (Half-Closure): 6.0s [BLOCK]       │ │ ------------------------- │ │
│ to watch reactive loop fire.  │  T_close:          10.0s [BLOCK]       │ │ --- RECEIPT TAPE #44 ---  │ │
│                               │                                        │ │ 12:45:36 UTC  [EXECUTED]  │ │
│ FUEL GAUGE (LASNA RESERVES)   │ LOOP ANATOMY (WATERFALL)               │ │ Orig: Uni Sepolia Blk 678 │ │
│ [████████████░░░░] 0.984 lREACT│ ├─▶ [T0] Origin Swap Confirmed (0.0s)  │ │ Lasna: Blk 8327773 (9s)   │ │
│ Debt: 0.000 lREACT  [NOMINAL] │ ├─▶ [T1] Lasna Event Reacted   (6.0s)  │ │ Dest: Base Sepolia (14s)  │ │
│                               │ ├─▶ [T2] Dest Callback Mined   (10.0s) │ │ Initial Gap: 952.2 bps   │ │
│                               │ └─▶ [T3] Equilibrium Restored  (10.0s) │ │ Final Gap:   0.0 bps     │ │
└───────────────────────────────┴────────────────────────────────────────┴───────────────────────────────┘
```

### 4.2 Screen 2: Run Report (`/runs/[id]`)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ HALFWAY // RUN REPORT: RUN-LOOP-45                                              [← Back to Console]    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ STATUS: VERIFIED ON CONSENSUS [● COMPLETE]              TIMESTAMP: 2026-11-14 12:46:38 UTC             │
│ ORIGIN: Base Sepolia (84532) ──▶ DESTINATION: Unichain Sepolia (1301) ──▶ REACTIVE LASNA (5318007)    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CHRONOLOGICAL LOOP DECOMPOSITION                                                                       │
│                                                                                                        │
│ [T0] 12:46:32 UTC | Base Sepolia Block 58692617                                                        │
│      Transaction Hash: 0x2149425c... [Basescan ↗]                                                      │
│      Initial Dislocation: 829.2 bps (Pool price: 1.0002 ──▶ 1.0831)                                    │
│      Observed Wall-Clock: 1794660392000 ms                                                             │
│                                                                                                        │
│   ▼  Elapsed Hop 1: 6.0s (Block Time) | 11.2s (Observer Wall-Clock)                                   │
│                                                                                                        │
│ [T1] 12:46:38 UTC | Reactive Lasna Block 8327822                                                       │
│      Transaction Hash: 0xb531fdcf... [Reactivescan ↗]                                                  │
│      Opportunity ID:   0x8f2a1b94...                                                                   │
│      Sizing Calculated: 0.005 ETH (Optimal Bounded) | Callbacks Dispatched: 2                          │
│                                                                                                        │
│   ▼  Elapsed Hop 2: 4.0s (Block Time) | 5.3s (Observer Wall-Clock)                                    │
│                                                                                                        │
│ [T2] 12:46:42 UTC | Unichain Sepolia Block 67807974                                                    │
│      Transaction Hash: 0xd47192aa... [Uniscan ↗]                                                       │
│      Callback Caller:  0x9299472A... (Authorized CallbackProxy)                                        │
│                                                                                                        │
│ [T3] 12:46:42 UTC | Equilibrium Restored                                                               │
│      Post-Trade Dislocation: 0.0 bps (Closed)                                                          │
│      Total Closure Time: 10.0s [BLOCK] | 16.5s [OBSERVER]                                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ECONOMICS & SETTLEMENT RECEIPT                                                                         │
│ Gross Capture: +0.0042 ETH | Leg Gas: 118,200 gas | System Debt Burn: 0.0472 lREACT | Net PnL: +10.5 bps│
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Screen 3: Latency Lab (`/lab`)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ HALFWAY // LATENCY LAB: EMPIRICAL BENCHMARK & SIMULATOR                                                │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ BENCHMARK HEADLINE METRICS (N = 32 Complete Loops, Verified on Consensus)                              │
│                                                                                                        │
│ HOP                                 | p50 (Block) | p90 (Block) | Max (Block) | p50 (Observer Wall)    │
│ Hop 1 (T0 ──▶ T1, Origin to Lasna)   | 7.0 s       | 8.0 s       | 11.0 s      | 11,272 ms [OBSERVER]  │
│ Hop 2 (T1 ──▶ T2, Lasna to Dest Leg) | 5.0 s       | 6.0 s       | 6.0 s       | 5,324 ms  [OBSERVER]  │
│ Hop 3 (T2 ──▶ T3, Gap Closed)        | 0.0 s       | 0.0 s       | 0.0 s       | 0 ms      [ATOMIC]    │
│ End-to-End (T0 ──▶ T3 Total Loop)    | 12.0 s      | 14.0 s      | 16.0 s      | 16,598 ms [OBSERVER]  │
│                                                                                                        │
│ Half-Closure Time (T½): 7.0 s [BLOCK]    | Total Closure Time (T_close): 12.0 s [BLOCK]                │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ COMPETITIVE LATENCY BUDGET SIMULATOR [SIMULATION MODEL]                                                │
│                                                                                                        │
│ Equation: Retained Share = (1/2)^(L / h)                                                               │
│                                                                                                        │
│ Halfway Reaction Latency (L):  [====|==============] 12.0 s   (Preset: [Measured p50 (12s)] [Legacy 7s])│
│ Competitor Half-Life (h):      [===|===============]  5.0 s   (Preset: [HFT 2s] [Bridge 5s] [Solv 7s]) │
│                                                                                                        │
│ RESULT:                                                                                                │
│ Retained Opportunity Share: [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 18.95% [SIMULATED]                  │
│ Theoretical Loss to Speed:  [░░░░░░░░████████████████████████████] 81.05% [SIMULATED]                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ TESTNET SPECIFICS & METHODOLOGY DISCLOSURES                                                            │
│ 1. Synthetic Pools: Test pairs have no organic external traders; gaps do not decay without Halfway.    │
│ 2. Relayer Batching: Hop 2 reflects asynchronous batching of official Reactive testnet relayer.       │
│ 3. EVM Clock Asynchrony: Inter-chain block headers drift by ±1-3s; wall-clock NTP is canonical truth. │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
