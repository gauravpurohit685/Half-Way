---
name: halfway-design-system
description: Design principles, typography, palette, and component rules for the Isotope Lab aesthetic.
---

# Halfway Design System ("Isotope Lab")

## Concept & Aesthetic
The UI evokes a precision nuclear physics laboratory instrument and field notebook. A price gap behaves like an unstable isotope decaying exponentially; Halfway is the high-speed scintillation detector recording each stage.

## Strict Bans
- NO blue-black, navy, or purple gradient backdrops.
- NO glassmorphism, blur cards, or glowing borders.
- NO generic stock 3D coins, rocket emojis, or crypto cliches.
- NO generic Inter / Roboto typography.
- NO unformatted or unaligned numbers; all metrics must use tabular figures.

## Palette
- **Light (Default / Primary)**:
  - Bone Paper: `#EFEAE0`
  - Deep Ink: `#15130F`
  - Graphite / Muted: `#5B5750`
  - Hairline Rule: `#CFC8B8`
- **Dark (Warm Charcoal)**:
  - Deep Charcoal: `#14110E`
  - Bone Text: `#EFEAE0`
  - Hairline Border: `#2E2A24`
- **Functional Signals (Identical across modes)**:
  - Signal Vermilion: `#FF4B1F` (Dislocation / Gap Open / Shock)
  - Reaction Lime: `#C9F23A` (Captured / Closed / Profitable)

## Typography
- **Headlines & Display**: `Instrument Serif` (italicized for emphasis)
- **Interface & Prose**: `Schibsted Grotesk`
- **Numerals, Code, Hashes**: `JetBrains Mono` with `font-variant-numeric: tabular-nums`

## Signature Components
1. **Decay Scope**: Graticule-backed live oscilloscope trace displaying real-time price gap in basis points.
2. **Loop Anatomy**: Stepped waterfall ticker detailing each hop (Origin -> Lasna -> Callback -> Gap Closed) with hash links.
3. **Isotope Pool Tiles**: Periodic-table style tiles displaying Chain symbol, Chain ID as "Atomic Number", pool address, and tick/price.
4. **Delay Slider**: Counterfactual slider (0–10s) visually eroding captured area, badged `SIMULATED`.
5. **Monospace Ledger Tape**: Reverse-chronological execution receipt feed.
