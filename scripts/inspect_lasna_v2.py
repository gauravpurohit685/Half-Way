import subprocess
import json

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
b_data = json.loads(subprocess.check_output([cast, "block", "8272012", "--json", "--rpc-url", env["RPC_REACTIVE_LASNA"]]).decode())["data"]

print("Transactions in block 8272012:", b_data.get("transactions"))
for tx in b_data.get("transactions", []):
    receipt = json.loads(subprocess.check_output([cast, "receipt", tx, "--json", "--rpc-url", env["RPC_REACTIVE_LASNA"]]).decode())
    print(f"Tx {tx}: Status = {receipt.get('status')}")
    for l in receipt.get("logs", []):
        print(f"  Log address: {l.get('address')}")
        print(f"  Topics: {l.get('topics')}")
        print(f"  Data: {l.get('data')}")
