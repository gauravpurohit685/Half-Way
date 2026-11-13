import subprocess
import json

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
tx = "0xafaec945bb067323d8058b9cb6043bda443032f44463c53cdaaa251ae20003ba"

tx_data = json.loads(subprocess.check_output([cast, "tx", tx, "--json", "--rpc-url", env["RPC_SEPOLIA"]]).decode())
print("To:", tx_data.get("to"))
print("From:", tx_data.get("from"))
print("Input selector:", tx_data.get("input", "")[:10])

receipt = json.loads(subprocess.check_output([cast, "receipt", tx, "--json", "--rpc-url", env["RPC_SEPOLIA"]]).decode())
print("Status:", receipt.get("status"))
print("Logs count:", len(receipt.get("logs", [])))
for l in receipt.get("logs", []):
    print("  Log addr:", l.get("address"))
    print("  Topics:", l.get("topics"))
