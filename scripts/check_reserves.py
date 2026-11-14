import urllib.request
import json
import subprocess
import os

cast_path = os.path.expanduser("~/.foundry/bin/cast")
pass_path = os.path.expanduser("~/.foundry/.halfway-pass")

account = subprocess.check_output(
    f"{cast_path} wallet address --account deployer --password-file {pass_path}",
    shell=True
).decode().strip()

print(f"Deployer Address: {account}")

rpcs = {
    "Base Sepolia": "https://sepolia.base.org",
    "Unichain Sepolia": "https://sepolia.unichain.org",
    "Reactive Lasna": "https://lasna-rpc.rnk.dev"
}

def get_bal(url, addr):
    req = urllib.request.Request(
        url,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getBalance","params":[addr, "latest"]}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Halfway/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        res = json.loads(r.read())
        return int(res["result"], 16) / 1e18

for name, url in rpcs.items():
    bal = get_bal(url, account)
    print(f"{name} Balance: {bal:.5f}")
