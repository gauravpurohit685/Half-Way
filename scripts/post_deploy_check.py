import json
import os
import subprocess
import sys

with open(".env") as f:
    env = dict(l.strip().split("=", 1) for l in f if "=" in l and not l.startswith("#"))
for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
deployer = env["DEPLOYER_ADDRESS"]

print("=== HALFWAY POST-DEPLOY CHECK ===")

deployments_dir = "deployments"
if not os.path.exists(deployments_dir):
    print("Error: No deployments directory found.")
    sys.exit(1)

base_file = os.path.join(deployments_dir, "base_sepolia.json")
uni_file = os.path.join(deployments_dir, "unichain_sepolia.json")
lasna_file = os.path.join(deployments_dir, "reactive_lasna.json")

for path, rpc, chain_name, expected_id in [
    (base_file, env["RPC_BASE_SEPOLIA"], "Base Sepolia", 84532),
    (uni_file, env["RPC_UNICHAIN_SEPOLIA"], "Unichain Sepolia", 1301),
    (lasna_file, env["RPC_REACTIVE_LASNA"], "Reactive Lasna", 5318007),
]:
    if not os.path.exists(path):
        print(f"Error: Missing deployment file {path}")
        sys.exit(1)

    cid = int(subprocess.check_output([cast, "chain-id", "--rpc-url", rpc]).decode().strip())
    assert cid == expected_id, f"Chain ID mismatch for {chain_name}: got {cid}, expected {expected_id}"
    print(f"✓ {chain_name} RPC responded with chain ID {cid}")

    with open(path) as f:
        data = json.load(f)

    for contract_name, address in data.get("contracts", {}).items():
        code = subprocess.check_output([cast, "code", address, "--rpc-url", rpc]).decode().strip()
        if len(code) <= 2:
            print(f"✗ {chain_name} {contract_name} at {address} has no bytecode!")
            sys.exit(1)
        print(f"✓ {chain_name} {contract_name}: {address} verified ({len(code)} bytes)")

print("\nALL POST-DEPLOY CHECKS PASSED!")
