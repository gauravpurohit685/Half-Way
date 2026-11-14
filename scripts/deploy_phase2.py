import json
import os
import subprocess
import sys
import time

forge = "/home/gaurav/.foundry/bin/forge"
cast = "/home/gaurav/.foundry/bin/cast"
passfile = "/home/gaurav/.foundry/.halfway-pass"

with open(".env") as f:
    env = dict(l.strip().split("=", 1) for l in f if "=" in l and not l.startswith("#"))
for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

rpc_lasna = env["RPC_REACTIVE_LASNA"]
rpc_base = env["RPC_BASE_SEPOLIA"]
rpc_uni = env["RPC_UNICHAIN_SEPOLIA"]
deployer = env["DEPLOYER_ADDRESS"]

os.makedirs("deployments", exist_ok=True)

print("========================================")
print("=== HALFWAY PHASE 2: SYSTEM DEPLOYMENT ===")
print("========================================")

# Step 1: Deploy HalfwayReactive on Reactive Lasna
print("\n[Step 1/4] Deploying HalfwayReactive on Reactive Lasna (5318007)...")
lasna_out = subprocess.check_output([
    forge, "script", "script/DeployHalfwayReactive.s.sol",
    "--rpc-url", rpc_lasna,
    "--account", "deployer",
    "--password-file", passfile,
    "--broadcast",
    "-vvv"
]).decode()

print(lasna_out)

# Parse reactive address from broadcast run latest
broadcast_lasna_path = "broadcast/DeployHalfwayReactive.s.sol/5318007/run-latest.json"
with open(broadcast_lasna_path) as f:
    b_lasna = json.load(f)

reactive_addr = None
for tx in b_lasna.get("transactions", []):
    if tx.get("contractName") == "HalfwayReactive":
        reactive_addr = tx.get("contractAddress")
        lasna_tx_hash = tx.get("hash")
        break

assert reactive_addr is not None, "Failed to find HalfwayReactive in broadcast logs!"
print(f"✓ HalfwayReactive deployed: {reactive_addr} (Tx: {lasna_tx_hash})")

# Step 2: Deploy Base Sepolia L2 (Tokens, Pool, Executor)
print(f"\n[Step 2/4] Deploying on Base Sepolia (84532) with Reactive {reactive_addr}...")
env_base = os.environ.copy()
env_base["REACTIVE_CONTRACT_ADDRESS"] = reactive_addr

base_out = subprocess.check_output([
    forge, "script", "script/DeployHalfwayL2.s.sol",
    "--rpc-url", rpc_base,
    "--account", "deployer",
    "--password-file", passfile,
    "--broadcast",
    "-vvv"
], env=env_base).decode()

print(base_out)

broadcast_base_path = "broadcast/DeployHalfwayL2.s.sol/84532/run-latest.json"
with open(broadcast_base_path) as f:
    b_base = json.load(f)

base_contracts = {}
for tx in b_base.get("transactions", []):
    cname = tx.get("contractName")
    if cname:
        base_contracts[cname] = tx.get("contractAddress")
        base_tx_hash = tx.get("hash")

print(f"✓ Base Sepolia contracts deployed: {base_contracts}")

# Step 3: Deploy Unichain Sepolia L2 (Tokens, Pool, Executor)
print(f"\n[Step 3/4] Deploying on Unichain Sepolia (1301) with Reactive {reactive_addr}...")
env_uni = os.environ.copy()
env_uni["REACTIVE_CONTRACT_ADDRESS"] = reactive_addr

uni_out = subprocess.check_output([
    forge, "script", "script/DeployHalfwayL2.s.sol",
    "--rpc-url", rpc_uni,
    "--account", "deployer",
    "--password-file", passfile,
    "--broadcast",
    "-vvv"
], env=env_uni).decode()

print(uni_out)

broadcast_uni_path = "broadcast/DeployHalfwayL2.s.sol/1301/run-latest.json"
with open(broadcast_uni_path) as f:
    b_uni = json.load(f)

uni_contracts = {}
for tx in b_uni.get("transactions", []):
    cname = tx.get("contractName")
    if cname:
        uni_contracts[cname] = tx.get("contractAddress")
        uni_tx_hash = tx.get("hash")

print(f"✓ Unichain Sepolia contracts deployed: {uni_contracts}")

# Save deployment files
with open("deployments/reactive_lasna.json", "w") as f:
    json.dump({
        "chainId": 5318007,
        "name": "Reactive Lasna",
        "contracts": {
            "HalfwayReactive": reactive_addr
        },
        "deploymentTx": lasna_tx_hash
    }, f, indent=2)

with open("deployments/base_sepolia.json", "w") as f:
    json.dump({
        "chainId": 84532,
        "name": "Base Sepolia",
        "contracts": base_contracts
    }, f, indent=2)

with open("deployments/unichain_sepolia.json", "w") as f:
    json.dump({
        "chainId": 1301,
        "name": "Unichain Sepolia",
        "contracts": uni_contracts
    }, f, indent=2)

# Step 4: Register pools on Reactive Lasna
print("\n[Step 4/4] Registering pools and subscribing on Reactive Lasna...")
env_reg = os.environ.copy()
env_reg["REACTIVE_CONTRACT_ADDRESS"] = reactive_addr
env_reg["BASE_POOL_ADDRESS"] = base_contracts["HalfPair"]
env_reg["BASE_EXECUTOR_ADDRESS"] = base_contracts["HalfwayExecutor"]
env_reg["UNICHAIN_POOL_ADDRESS"] = uni_contracts["HalfPair"]
env_reg["UNICHAIN_EXECUTOR_ADDRESS"] = uni_contracts["HalfwayExecutor"]

reg_out = subprocess.check_output([
    forge, "script", "script/RegisterPoolsLasna.s.sol",
    "--rpc-url", rpc_lasna,
    "--account", "deployer",
    "--password-file", passfile,
    "--broadcast",
    "-vvv"
], env=env_reg).decode()

print(reg_out)

print("\n=========================================")
print("=== DEPLOYMENT COMPLETED SUCCESSFULLY ===")
print("=========================================")
