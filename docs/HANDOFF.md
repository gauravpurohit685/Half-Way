# Gate D Handoff: Phase 2 Core Contracts & Verification

**Project:** Halfway — Reactive Omni Price-Gap Capture Vault  
**Phase Completed:** Phase 2 (Core Contracts, Tests, Deployment Tooling & Live On-Chain Validation)  
**Status:** Ready for Gate D Acceptance  

---

## 1. Final Architecture & On-Chain Addresses

- **Reactive Lasna (`5318007`):**
  - `HalfwayReactive`: [`0x61a66307fa18203110f73745628252592d975c9f`](https://lasna.reactivescan.io/address/0x61a66307fa18203110f73745628252592d975c9f)
  - Features: Omni event subscriptions (`SYSTEM.subscribe`), price normalisation (18 decimals), fee hurdles ($30+30+10=70\text{ bps}$), cooldown (5s), max staleness (600s), closed-form bounded trade sizing, and callback requests (`SYSTEM.requestCallbackV_1_0`).
- **Base Sepolia (`84532`):**
  - `HalfPair` (mHALF / mWETH): [`0x781264ed18eb99763ec0a5be964fafcfb86e9017`](https://sepolia.basescan.org/address/0x781264ed18eb99763ec0a5be964fafcfb86e9017)
  - `HalfwayExecutor` (Vault): [`0x0880e110103156af8c9df5a2e929eb96cd7a1d74`](https://sepolia.basescan.org/address/0x0880e110103156af8c9df5a2e929eb96cd7a1d74)
  - Proxy: `0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6`
- **Unichain Sepolia (`1301`):**
  - `HalfPair` (mHALF / mWETH): [`0x3f6bfb643f9d4b2a03062333344abd80644d33ae`](https://sepolia.uniscan.xyz/address/0x3f6bfb643f9d4b2a03062333344abd80644d33ae)
  - `HalfwayExecutor` (Vault): [`0x47489fba9d8da11c189ec8b8bee0839da3bb6ba5`](https://sepolia.uniscan.xyz/address/0x47489fba9d8da11c189ec8b8bee0839da3bb6ba5)
  - Proxy: `0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4`

---

## 2. Test Suite & Invariant Verification
- **Test Results:** 21 tests passed across 6 test suites (0 failed).
- **Invariant Solvency:** 128,000 calls verified in Foundry:
  1. `invariant_TotalSharesConservation`: Shares strictly conserved ($S_{\text{total}} = \sum S_{\text{user}} + 1000$).
  2. `invariant_VaultSolvency`: Vault assets strictly cover all shares at all times.
  3. `invariant_UserSharesBounded`: User cannot withdraw beyond their share.
- **Coverage:** Core contracts achieve >88–90% branch/statement coverage.
- **Security & Slither:** Threat model documented in [`docs/SECURITY.md`](file:///d:/MERN%20PROJECTS/REACTIVE/docs/SECURITY.md). ReentrancyGuard, SafeERC20, Ownable2Step, exact approvals, and custom errors enforced.

---

## 3. Measured Live Latencies (Exit Test)
- **RUN-01 (Base Sepolia Origin):** Tx `0xa0d3...8eb6` $\to$ Lasna Tx `0x2173...1145` (Block `8317184`). Latency: **3s** on-chain, 11.25s observer.
- **RUN-02 (Unichain Origin):** Tx `0x675b...3e3d` $\to$ Lasna Tx `0x3814...c7a0` (Block `8317201`). Latency: **24s** on-chain, 25.10s observer.
- **RUN-03 (Base Sepolia Origin):** Tx `0x1bf7...db31` $\to$ Lasna Tx `0x522c...e3cc` (Block `8317266`). Latency: **2s** on-chain, 7.95s observer.
- **RUN-04 (Base Sepolia Origin):** Tx `0xf667...7d7` $\to$ Lasna Tx `0xa10a...a657` (Block `8317297`). Latency: **2s** on-chain, 5.77s observer.
- **Negative Test:** Sub-threshold spread correctly suppressed by hurdle logic (**0 callbacks dispatched**).
- **Replay & Auth Test:** Non-proxy and replayed `opportunityId` calls strictly rejected.

---

## 4. Known Limitations & Edge Cases
- Testnet relayer on destination proxies operates asynchronously with variable queueing latency; Lasna reactive transactions are immediate (2–3s).
- Constant-product pools use discrete ticks from `Sync` reserves.
- Virtual liquidity offset (`MINIMUM_LIQUIDITY = 1000`) locks initial wei against first-depositor inflation.

---

## 5. Next Tasks for Phase 3 (Indexer + Latency Lab)
1. Build TypeScript daemon indexer (`services/indexer/`) using SQLite / Ponder to ingest `Sync`, `OpportunityDetected`, `CallbackDispatched`, and `LegExecuted` events.
2. Implement half-life ($\tau_{1/2}$) exponential decay calculation engine ($\Delta P(t) = \Delta P_0 e^{-\lambda t}$).
3. Implement counterfactual legacy latency simulator ($7\text{s}$ comparative loss model badged `SIMULATED`).
4. Expose REST/WebSocket endpoint for the Frontend Isotope Lab.
