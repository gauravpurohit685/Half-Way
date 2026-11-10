# /deploy-testnet Workflow

## Purpose
Deploy the Halfway contracts across Base Sepolia, Unichain Sepolia, and Reactive Lasna using Foundry scripts and verified keystore credentials.

## Steps
1. Verify network health and chain IDs (`84532`, `1301`, `5318007`).
2. Verify wallet balances meet required minimums (0.03 ETH per L2, 10 lREACT on Lasna).
3. Deploy `HalfLifeExecutor` to Base Sepolia:
   ```bash
   forge script script/DeployExecutor.s.sol --rpc-url $RPC_BASE_SEPOLIA --account deployer --password-file ~/.foundry/.halfway-pass --broadcast
   ```
4. Deploy `HalfLifeExecutor` to Unichain Sepolia:
   ```bash
   forge script script/DeployExecutor.s.sol --rpc-url $RPC_UNICHAIN_SEPOLIA --account deployer --password-file ~/.foundry/.halfway-pass --broadcast
   ```
5. Deploy `HalfLifeReactive` to Reactive Lasna:
   ```bash
   forge script script/DeployReactive.s.sol --rpc-url $RPC_REACTIVE_LASNA --account deployer --password-file ~/.foundry/.halfway-pass --broadcast
   ```
6. Fund `HalfLifeReactive` with initial operational lREACT (max 2 lREACT).
7. Save deployed addresses to `deployments/<chain_id>.json`.
8. Append deployment records to `docs/AGENT_LOG.md`.
