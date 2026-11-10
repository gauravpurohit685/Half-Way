import subprocess
import json

cast_bin = "/home/gaurav/.foundry/bin/cast"
rpc = "https://lasna-rpc.rnk.dev"

res = subprocess.check_output([cast_bin, "block", "latest", "--json", "--rpc-url", rpc]).decode()
data = json.loads(res)["data"]
print("Data keys:", list(data.keys()))
print("Number:", data.get("number"))
print("Timestamp:", data.get("timestamp"))
