import os
import subprocess
import re

env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("\"'").strip()

cast_bin = "/home/gaurav/.foundry/bin/cast"

rpcs = {
    "Sepolia": env.get("RPC_SEPOLIA"),
    "Base Sepolia": env.get("RPC_BASE_SEPOLIA"),
    "Unichain Sepolia": env.get("RPC_UNICHAIN_SEPOLIA"),
    "Reactive Lasna": env.get("RPC_REACTIVE_LASNA")
}

deployer = env.get("DEPLOYER_ADDRESS")
test_user = env.get("TEST_USER_ADDRESS")

print(f"Deployer address configured: {bool(deployer)}")
print(f"Test user address configured: {bool(test_user)}")

for name, rpc in rpcs.items():
    if not rpc:
        print(f"[{name}] RPC missing!")
        continue
    # Chain ID
    try:
        res = subprocess.run([cast_bin, "chain-id", "--rpc-url", rpc], capture_output=True, text=True, check=True)
        chain_id = res.stdout.strip()
    except Exception as e:
        chain_id = f"ERROR: {e}"

    # Deployer balance
    dep_bal = "N/A"
    if deployer:
        try:
            res = subprocess.run([cast_bin, "balance", deployer, "--rpc-url", rpc, "--ether"], capture_output=True, text=True, check=True)
            dep_bal = res.stdout.strip()
        except Exception as e:
            dep_bal = f"ERROR: {e}"

    # Test user balance
    user_bal = "N/A"
    if test_user:
        try:
            res = subprocess.run([cast_bin, "balance", test_user, "--rpc-url", rpc, "--ether"], capture_output=True, text=True, check=True)
            user_bal = res.stdout.strip()
        except Exception as e:
            user_bal = f"ERROR: {e}"

    print(f"[{name}] Chain ID: {chain_id} | Deployer Bal: {dep_bal} | Test User Bal: {user_bal}")
