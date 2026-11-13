import subprocess
import json

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
tx = "0xb68a801135990b88ea945da3298112fdfa5133a9a6ea0d7d79499af8b74ba7b6"

receipt = json.loads(subprocess.check_output([cast, "receipt", tx, "--json", "--rpc-url", env["RPC_REACTIVE_LASNA"]]).decode())
print("Status:", receipt.get("status"))
print("Gas used:", receipt.get("gasUsed"))
print("Logs count:", len(receipt.get("logs", [])))
for i, l in enumerate(receipt.get("logs", [])):
    print(f"Log {i}:")
    print("  Address:", l.get("address"))
    print("  Topics:", l.get("topics"))
    print("  Data:", l.get("data"))
