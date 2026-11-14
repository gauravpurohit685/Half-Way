# Agent On-Chain Audit Log

| Timestamp (UTC) | Chain | Purpose | Tx Hash / Action | Amount Spent | Balance Remaining |
|---|---|---|---|---|---|
| 2026-11-10 19:15 | All | Phase 0 verification: read-only checks | N/A (read-only queries) | 0.000 ETH | Base: 0.150 ETH, Uni: 0.150 ETH, Lasna: 52.50 lREACT |
| 2026-11-10 19:40 | Base Sepolia | Deploy HelloOrigin.sol | `0xa55092852d45ec1e596df7af4dd145fe0f27f7a9dd2e88f04d939d4a867780cc` | ~0.000001 ETH | Base: 0.150 ETH |
| 2026-11-10 19:42 | Unichain Sepolia | Deploy HelloDestination.sol | `0x79415396249b07e72c6fcd54d70e58d8e7d141fdfa49931adb82c1133627f674` | ~0.000001 ETH | Uni: 0.150 ETH |
| 2026-11-10 19:44 | Reactive Lasna | Deploy HelloReactive.sol | `0x9580f97acfdf73fee2444a46876ae0e6ea7b514416370b40422f74e5f9ff8b39` | ~0.001 lREACT | Lasna: 52.49 lREACT |
| 2026-11-10 19:45 | Reactive Lasna | Fund HelloReactive with lREACT | `0x42f7027d7c2b535d46816ecdf4347209ae8433d5ba9a35e7df802951e7fb8fc3` | 1.000 lREACT | Lasna: 51.49 lREACT |
| 2026-11-10 19:50 | Base Sepolia | Hello-Loop V1 Ping (`ping(1001)`) | `0xe96c8bd4b55f8181c813a0312034d26ecb2cffe6c629ae12ffc839a1fac3aa7d` | ~0.0000005 ETH | Base: 0.150 ETH |
| 2026-11-10 19:50 | Reactive Lasna | Reactive Omni Reaction V1 (System) | `0xb7b3b417d320b9510490f6df590fedbd199965507285043b7488e872dea7fdc5` | Gas from contract | Contract lREACT reserve |
| 2026-11-13 19:58 | Sepolia | Deploy HelloDestination.sol (Sepolia) | `0x809a95e59d3378cd01794b628000418d2c5e3e150b539ddb5da2659234a8befb` | ~0.0001 ETH | Sepolia: 1.349 ETH |
| 2026-11-13 20:00 | Reactive Lasna | Deploy HelloReactiveV2.sol | `0x72a7571333aa7d66ed7c7c21180a03dfe9635c98583bb27ad798b867f2ce8fee` | ~0.001 lREACT | Lasna: 51.48 lREACT |
| 2026-11-13 20:01 | Reactive Lasna | Fund HelloReactiveV2 with lREACT | `0xa71ebfe8c40ff23a9d9422df50c3132e4d25fa0a12e84d4fa716fb8e154f9a39` | 1.000 lREACT | Lasna: 50.48 lREACT |
| 2026-11-13 20:19 | Base Sepolia | Hello-Loop V2 Ping (`ping(3003)`) | `0x781ce57c8fb034994a0e103051ff85f676f44a8e7f8b9a32fc569a9b540ee280` | ~0.0000005 ETH | Base: 0.150 ETH |
| 2026-11-13 20:19 | Reactive Lasna | Reactive Omni Reaction V2 (System) | `0xb68a801135990b88ea945da3298112fdfa5133a9a6ea0d7d79499af8b74ba7b6` | Gas from contract | Contract lREACT reserve |
| 2026-11-14 09:23 | Reactive Lasna | Deploy HalfwayReactive & Fund 1.0 lREACT | `0xf4d53da71a755a85834b28a4908ed535445c3ad72066d72c7242303c4450dfe1` | 1.001 lREACT | Lasna: 49.38 lREACT |
| 2026-11-14 09:23 | Base Sepolia | Deploy Tokens, HalfPair, HalfwayExecutor | Multi-tx batch (DeployHalfwayL2) | ~0.00003 ETH | Base: 0.1499 ETH |
| 2026-11-14 09:24 | Unichain Sepolia | Deploy Tokens, HalfPair, HalfwayExecutor | Multi-tx batch (DeployHalfwayL2) | ~0.000002 ETH | Uni: 0.1499 ETH |
| 2026-11-14 09:24 | Reactive Lasna | Register Pools on Lasna | `0x780d9fee474ee2190cc5b08715714beb9d4a2eabfb33424fc75f5d9124936f22` | ~0.001 lREACT | Lasna: 49.37 lREACT |
| 2026-11-14 09:37 | Base Sepolia | Live Shock 1 Swap (Origin $T_0$) | `0xa0d332e4e8ed2571ffacdc4d1dc6c88672a77316d86cdb037efe7c23606e8eb6` | ~0.0000005 ETH | Base: 0.1499 ETH |
| 2026-11-14 09:37 | Reactive Lasna | Live Opportunity #1 Reaction ($T_1$) | `0x217390510ea1c4735f841357f782859dc6c9c625aef71b8a3ac0ba6e9fb51145` | Gas from contract | Contract lREACT reserve |
| 2026-11-14 09:38 | Unichain Sepolia | Live Shock 2 Swap (Origin $T_0$) | `0x675b38ac3d8260958544d1f2c35537433c2aee6fb1ea818e1318cd9f5c183e3d` | ~0.0000005 ETH | Uni: 0.1499 ETH |
| 2026-11-14 09:38 | Reactive Lasna | Live Opportunity #2 Reaction ($T_1$) | `0x3814c2be2ea2882aa194a480a10f49d9fb4b584bd88792f45effbb51d652c7a0` | Gas from contract | Contract lREACT reserve |
| 2026-11-14 09:39 | Base Sepolia | Live Shock 3 Swap (Origin $T_0$) | `0x1bf797e5a2eb822d6ae732ba5143ce378c60d09eb1d72a515c058de026b6db31` | ~0.0000005 ETH | Base: 0.1499 ETH |
| 2026-11-14 09:39 | Reactive Lasna | Live Opportunity #3 Reaction ($T_1$) | `0x522cf19bac8b0279afa3a40d06e2d8b3255cc0b96f1b56bcabcf3e2de173e3cc` | Gas from contract | Contract lREACT reserve |
| 2026-11-14 09:40 | Base Sepolia | Live Shock 4 Swap (Origin $T_0$) | `0xf667ce960c364a62d1b59ce4f30881878e72eb3930b88ba6f20cd67e4cfbf7d7` | ~0.0000005 ETH | Base: 0.1499 ETH |
| 2026-11-14 09:40 | Reactive Lasna | Live Opportunity #4 Reaction ($T_1$) | `0xa10ab866f1898ddfc832878d46f380fe2abb265fe3bca91d48ffb646cea0a657` | Gas from contract | Contract lREACT reserve |
| 2026-11-14 09:42 | Base Sepolia | Negative Test Sub-threshold Swap | `0xca0b91dc3895e34f71a067ff25925ffec24045f2a1bce471d8db0cf78ee5ff33` | ~0.0000005 ETH | Base: 0.1499 ETH |
