import subprocess
import json

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"

# Base Sepolia callback proxy: 0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6
proxy_base = "0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6"
latest_base = int(subprocess.check_output([cast, "block-number", "--rpc-url", env["RPC_BASE_SEPOLIA"]]).decode().strip())
print(f"Latest Base Sepolia block: {latest_base}")

# Query logs from proxy on Base Sepolia for the last 5000 blocks
try:
    logs = subprocess.check_output([
        cast, "logs",
        "--address", proxy_base,
        "--from-block", str(latest_base - 1000),
        "--to-block", str(latest_base),
        "--json",
        "--rpc-url", env["RPC_BASE_SEPOLIA"]
    ]).decode()
    logs_data = json.loads(logs)
    print(f"Base Sepolia proxy logs count in last 1000 blocks: {len(logs_data)}")
except Exception as e:
    print("Error querying Base logs:", e)

# Unichain Sepolia callback proxy: 0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4
proxy_uni = "0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4"
latest_uni = int(subprocess.check_output([cast, "block-number", "--rpc-url", env["RPC_UNICHAIN_SEPOLIA"]]).decode().strip())
print(f"Latest Unichain Sepolia block: {latest_uni}")
try:
    logs = subprocess.check_output([
        cast, "logs",
        "--address", proxy_uni,
        "--from-block", str(latest_uni - 1000),
        "--to-block", str(latest_uni),
        "--json",
        "--rpc-url", env["RPC_UNICHAIN_SEPOLIA"]
    ]).decode()
    logs_data = json.loads(logs)
    print(f"Unichain Sepolia proxy logs count in last 1000 blocks: {len(logs_data)}")
except Exception as e:
    print("Error querying Uni logs:", e)
