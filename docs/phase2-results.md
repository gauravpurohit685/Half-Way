# Phase 2 Verification & Live Testnet Results

This document records the empirical results of **Phase 2 (Core Contracts & Verification)** for the **Halfway** cross-chain arbitrage vault.

---

## 1. Deployed Contract Addresses

### Reactive Lasna (`5318007`)
- **`HalfwayReactive`**: [`0x61a66307fa18203110f73745628252592d975c9f`](https://lasna.reactivescan.io/address/0x61a66307fa18203110f73745628252592d975c9f)
  - Deployment Tx: `0xf4d53da71a755a85834b28a4908ed535445c3ad72066d72c7242303c4450dfe1`
  - Pre-funded Reserve: `1.0 lREACT`
  - Pool Registration Tx: `0x780d9fee474ee2190cc5b08715714beb9d4a2eabfb33424fc75f5d9124936f22`

### Base Sepolia (`84532`)
- **`HalfPair` (mHALF / mWETH)**: [`0x781264ed18eb99763ec0a5be964fafcfb86e9017`](https://sepolia.basescan.org/address/0x781264ed18eb99763ec0a5be964fafcfb86e9017)
- **`HalfwayExecutor` (Vault)**: [`0x0880e110103156af8c9df5a2e929eb96cd7a1d74`](https://sepolia.basescan.org/address/0x0880e110103156af8c9df5a2e929eb96cd7a1d74)
- **`MockERC20` (Token 0)**: `0x3f6BFb643f9D4b2a03062333344aBD80644D33Ae`
- **`MockERC20` (Token 1)**: `0x47489FbA9D8DA11c189ec8B8bEE0839da3Bb6bA5`
- **Callback Proxy**: `0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6`

### Unichain Sepolia (`1301`)
- **`HalfPair` (mHALF / mWETH)**: [`0x3f6bfb643f9d4b2a03062333344abd80644d33ae`](https://sepolia.uniscan.xyz/address/0x3f6bfb643f9d4b2a03062333344abd80644d33ae)
- **`HalfwayExecutor` (Vault)**: [`0x47489fba9d8da11c189ec8b8bee0839da3bb6ba5`](https://sepolia.uniscan.xyz/address/0x47489fba9d8da11c189ec8b8bee0839da3bb6ba5)
- **`MockERC20` (Token 0)**: `0x61A66307Fa18203110f73745628252592d975c9F`
- **`MockERC20` (Token 1)**: `0x644b88B9081968D5f72F02f467D4d7d22a5d44D5`
- **Callback Proxy**: `0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4`

---

## 2. On-Chain Live Execution Loops

| Run ID | Origin Chain | Origin Tx ($T_0$) | Origin Block / $T_0$ | Lasna Tx ($T_1$) | Lasna Block / $T_1$ | Reactive Delay ($T_1 - T_0$) | Observer Latency | Opportunity ID | Status |
|---|---|---|---|---|---|---|---|---|---|
| **RUN-LOOP-01** | Base Sepolia (`84532`) | `0xa0d3...8eb6` | Blk `58636063` / `1794649081` | `0x2173...1145` | Blk `8317184` / `1794649084` | **3 s** | 11.25 s | `0x652e...4bc1` | Verified |
| **RUN-LOOP-02** | Unichain Sepolia (`1301`) | `0x675b...3e3d` | Blk `67796549` / `1794648977` | `0x3814...c7a0` | Blk `8317201` / `1794649001` | **24 s** | 25.10 s | `0x5fb3...264f` | Verified |
| **RUN-LOOP-03** | Base Sepolia (`84532`) | `0x1bf7...db31` | Blk `58636168` / `1794649102` | `0x522c...e3cc` | Blk `8317266` / `1794649104` | **2 s** | 7.95 s | `0xce39...4c4` | Verified |
| **RUN-LOOP-04** | Base Sepolia (`84532`) | `0xf667...7d7` | Blk `58636517` / `1794649172` | `0xa10a...a657` | Blk `8317297` / `1794649174` | **2 s** | 5.77 s | `0xd591...669` | Verified |

---

## 3. Negative & Replay Validation Results

### 3.1 Negative Test (Sub-threshold Spread)
- **Test:** Dislocation evaluated against a higher hurdle (threshold = 5000 bps).
- **Result:** Origin swap executed and intercepted on Lasna via `react()`, but spread ($35\%$) was strictly below hurdle ($50\%$). `totalOpportunitiesDetected` remained constant. **Zero callbacks dispatched.**
- **Status:** **PASS**

### 3.2 Replay Protection & Unauthorized Callback Test
- **Test:** Direct invocation of `HalfwayExecutor.executeCallback()` by an unauthenticated address and replayed `opportunityId`.
- **Result:** Transaction reverted with `UnauthorizedCallbackCaller`. Replay mapping verified on-chain.
- **Status:** **PASS**

---

## 4. Test Suite Summary
- **Total Unit & Fuzz Tests:** 20 tests across AMM, Vault, and Reactive engine (**100% PASS**).
- **Invariant Tests:** 128,000 randomized state transitions (**100% PASS**, zero broken invariants).
- **Invariants Verified:**
  1. `invariant_TotalSharesConservation`: Vault total supply strictly equals user shares plus locked minimum liquidity.
  2. `invariant_VaultSolvency`: Vault assets strictly cover all minted shares at all times.
  3. `invariant_UserSharesBounded`: No user can ever possess more shares than total supply.
