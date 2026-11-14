import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load root .env
const rootEnvPath = path.resolve(__dirname, '../../../.env');
if (fs.existsSync(rootEnvPath)) {
  dotenv.config({ path: rootEnvPath });
} else {
  dotenv.config();
}

function loadDeployment(filename: string) {
  const p = path.resolve(__dirname, '../../../deployments', filename);
  if (!fs.existsSync(p)) {
    throw new Error(`Deployment file missing: ${p}`);
  }
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

export const baseSepoliaDeployment = loadDeployment('base_sepolia.json');
export const unichainSepoliaDeployment = loadDeployment('unichain_sepolia.json');
export const reactiveLasnaDeployment = loadDeployment('reactive_lasna.json');

// Use public RPCs by default to protect free-tier Alchemy quotas and 10-block limits
export const config = {
  port: parseInt(process.env.PORT || '3001', 10),
  dbPath: process.env.DB_PATH || path.resolve(__dirname, '../../../data/halfway.db'),
  chains: {
    baseSepolia: {
      id: 84532,
      name: 'Base Sepolia',
      rpcUrl: 'https://sepolia.base.org',
      fallbackRpc: 'https://sepolia.base.org',
      explorerUrl: 'https://sepolia.basescan.org',
      startBlock: baseSepoliaDeployment.startBlock || 58631867,
      contracts: baseSepoliaDeployment.contracts,
      pollIntervalMs: 2000,
      chunkSize: 100,
    },
    unichainSepolia: {
      id: 1301,
      name: 'Unichain Sepolia',
      rpcUrl: 'https://sepolia.unichain.org',
      fallbackRpc: 'https://sepolia.unichain.org',
      explorerUrl: 'https://sepolia.uniscan.xyz',
      startBlock: unichainSepoliaDeployment.startBlock || 67795832,
      contracts: unichainSepoliaDeployment.contracts,
      pollIntervalMs: 2000,
      chunkSize: 100,
    },
    reactiveLasna: {
      id: 5318007,
      name: 'Reactive Lasna',
      rpcUrl: process.env.RPC_REACTIVE_LASNA || 'https://lasna-rpc.rnk.dev',
      fallbackRpc: 'https://lasna-rpc.rnk.dev',
      explorerUrl: 'https://lasna.reactivescan.io',
      startBlock: reactiveLasnaDeployment.startBlock || 8316383,
      contracts: reactiveLasnaDeployment.contracts,
      pollIntervalMs: 1000,
      chunkSize: 100,
    },
  },
};
