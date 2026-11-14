import subprocess

with open(".env") as f:
    env = dict(l.strip().split("=", 1) for l in f if "=" in l and not l.startswith("#"))
for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
addr = env["DEPLOYER_ADDRESS"]

for name, rpc in [
    ("Base Sepolia", env["RPC_BASE_SEPOLIA"]),
    ("Unichain Sepolia", env["RPC_UNICHAIN_SEPOLIA"]),
    ("Reactive Lasna", env["RPC_REACTIVE_LASNA"]),
]:
    nonce = subprocess.check_output([cast, "nonce", addr, "--rpc-url", rpc]).decode().strip()
    bal = subprocess.check_output([cast, "balance", addr, "--ether", "--rpc-url", rpc]).decode().strip()
    print(f"{name}: nonce={nonce}, balance={bal}")
