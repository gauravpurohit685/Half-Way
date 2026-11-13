import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
addr = env["DEPLOYER_ADDRESS"]

chains = [
    ("Ethereum Sepolia", env["RPC_SEPOLIA"]),
    ("Base Sepolia", env["RPC_BASE_SEPOLIA"]),
    ("Unichain Sepolia", env["RPC_UNICHAIN_SEPOLIA"]),
    ("Reactive Lasna", env["RPC_REACTIVE_LASNA"]),
]

for name, rpc in chains:
    bal = subprocess.check_output([cast, "balance", addr, "--ether", "--rpc-url", rpc]).decode().strip()
    print(f"{name}: {bal}")
