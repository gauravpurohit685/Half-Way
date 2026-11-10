# /ui-verify Workflow

## Purpose
Rigorously verify UI rendering, responsiveness, keyboard accessibility, theme switching, and real-time state hydration.

## Verification Checklist
1. **Responsive Viewports**:
   - Mobile: 390px
   - Tablet: 768px
   - Desktop: 1440px
2. **Design System Conformance**:
   - Palette: Bone `#EFEAE0`, Deep Ink `#15130F`, Vermilion `#FF4B1F`, Lime `#C9F23A`.
   - Typography: Instrument Serif headlines, Schibsted Grotesk UI, JetBrains Mono tabular figures.
   - Zero banned elements (no blue-black gradients, no glassmorphism, no neon glows).
3. **Interactive Elements**:
   - Decay Scope renders live trace.
   - Isotope tiles hydrate live pool ticks/prices.
   - Loop Anatomy links out to verified block explorers.
   - Delay slider operates smoothly with explicit `SIMULATED` badging.
4. **Accessibility (WCAG AA)**:
   - Visible focus rings.
   - Valid ARIA roles and labels.
   - `prefers-reduced-motion` compliance.
