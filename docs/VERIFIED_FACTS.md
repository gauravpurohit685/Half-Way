# Verified Facts

This file records empirical testnet measurements, verified contract addresses, and architecture parameters. Every entry is backed by on-chain queries or official source code inspection.

---

### Fact 1: Active Chain IDs and RPC Connectivity
- **Question:** Do all configured testnet RPCs respond with the expected chain IDs?
- **Method:** `cast chain-id --rpc-url <URL>` across all 4 configured endpoints.
- **Result:**
  - Sepolia: `11155111`
  - Base Sepolia: `84532`
  - Unichain Sepolia: `1301`
  - Reactive Lasna: `5318007`
- **Conclusion:** All network endpoints are operational and strictly match whitelist.

---

### Fact 2: Wallet Balances & Keystore Setup
- **Question:** Does the local keystore `deployer` match `DEPLOYER_ADDRESS` and satisfy reserve limits?
- **Method:** `cast wallet address --account deployer --password-file ~/.foundry/.halfway-pass` compared to `.env`, and `cast balance` queried for each network.
- **Result:**
  - Keystore address matches `DEPLOYER_ADDRESS`: `True`
  - Base Sepolia: Deployer = `0.150 ETH` (test user = `0.150 ETH`)
  - Unichain Sepolia: Deployer = `0.150 ETH` (test user = `0.1499 ETH`)
  - Reactive Lasna: Deployer = `52.500 lREACT`
  - Ethereum Sepolia: Deployer = `1.3499 ETH` (reserve)
- **Conclusion:** Balances satisfy the minimum reserve limits (>= 0.03 ETH per L2, >= 10 lREACT on Lasna).

---

### Fact 3: Reactive Lasna Block Time
- **Question:** What is the actual block time on Reactive Lasna post-Omni migration?
- **Method:** Queried 15 consecutive blocks (`8024594` to `8024609`) on `https://lasna-rpc.rnk.dev` using `cast block --json`.
- **Result:** Consecutive timestamp deltas: `[1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]` seconds. Average block time = `1.07 seconds`.
- **Conclusion:** Lasna operates with ~1s block times under CometBFT consensus.

---

### Fact 4: Reactive Omni System Contract & Callback Architecture
- **Question:** Does Reactive Omni use legacy precompiles (`0x000...fffFfF`) or the modern Omni system contract (`0x8888888888888888888888888888888888888888`), and how are callbacks requested?
- **Method:** Inspected official `Reactive-Network/reactive-lib-omni` repository source code (`AbstractReactive.sol`, `ISystemContract.sol`, `AbstractCallback.sol`) and queried code lengths on Lasna.
- **Result:**
  - `AbstractReactive.sol` defines `ISystemContract internal constant SYSTEM = ISystemContract(payable(0x8888888888888888888888888888888888888888));`
  - Bytecode length at `0x8888888888888888888888888888888888888888` on Lasna is 480 bytes.
  - Event subscriptions use `SYSTEM.subscribe(chainId, contract, topic0, topic1, topic2, topic3)`.
  - Callbacks are requested via `SYSTEM.requestCallbackV_1_0(config)`. The legacy pattern `emit Callback(...)` is deprecated.
  - Destination callback authentication uses modifier `onlyCallbackSender(address)` inside `AbstractCallback.sol`.
- **Conclusion:** Reactive Omni requires `@reactive-lib-omni` patterns. No legacy `vm` or `emit Callback` patterns may be used.

---

### Fact 5: Destination Callback Proxies
- **Question:** What are the verified callback proxy contract addresses on Base Sepolia and Unichain Sepolia?
- **Method:** Verified deployed bytecode on both chains.
- **Result:**
  - Base Sepolia Callback Proxy: `0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6` (code length: 12,626 bytes)
  - Unichain Sepolia Callback Proxy: `0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4` (code length: 12,626 bytes)
  - Sepolia Callback Proxy: `0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA` (code length: 6,658 bytes)
- **Conclusion:** Both target chains possess identical, deployed Reactive callback proxies.

---

### Fact 6: On-Chain DEX Liquidity Pools
- **Question:** Do active Uniswap V3 pools exist on both Base Sepolia and Unichain Sepolia for WETH/USDC?
- **Method:** Queried `UniswapV3Factory.getPool()` on Base Sepolia (`0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24`) and Unichain Sepolia (`0x1F98431c8aD98523631AE4a59f267346ea31F984`) for WETH (`0x4200000000000000000000000000000000000006`) against USDC (`0x036CbD53842c5426634e7929541eC2318f3dCF7e` on Base, `0x31d0220469e10c4E71834a79b1f276d740d3768F` on Unichain).
- **Result:**
  - Base Sepolia 500 fee pool: `0x94bfc0574FF48E92cE43d495376C477B1d0EEeC0` (active liquidity: 1.34e13, tick: 202941)
  - Base Sepolia 3000 fee pool: `0x46880b404CD35c165EDdefF7421019F8dD25F4Ad` (active liquidity: 3.31e14, tick: 203377)
  - Unichain Sepolia 500 fee pool: `0xBeAD5792bB6C299AB11Eaa425aC3fE11ebA47b3B` (active liquidity: 1.72e13, tick: 187223)
  - Unichain Sepolia 3000 fee pool: `0x8F463126bBEA80A10DF9Bf6FF5455B6B0292B34e` (active liquidity: 6.60e13, tick: 171494)
- **Conclusion:** Both chains possess operational Uniswap V3 pools with liquidity.
