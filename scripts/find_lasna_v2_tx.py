import subprocess
import json

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
rec = "0x644b88b9081968d5f72f02f467d4d7d22a5d44d5"

logs_res = subprocess.check_output([
    cast, "logs",
    "--address", rec,
    "--from-block", "8272000",
    "--to-block", "latest",
    "--json",
    "--rpc-url", env["RPC_REACTIVE_LASNA"]
]).decode()

logs = json.loads(logs_res)
print(f"Found {len(logs)} logs for HelloReactiveV2:")
for l in logs:
    print("Log:")
    print("  Tx Hash:", l.get("transactionHash"))
    print("  Block Number:", int(l.get("blockNumber", "0x0"), 16))
    print("  Topics:", l.get("topics"))
    print("  Data:", l.get("data"))
