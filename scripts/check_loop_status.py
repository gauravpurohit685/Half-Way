import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
addr = "0xc471090292e60580625fb0b796199f253c3d8f90"

pings = subprocess.check_output([cast, "call", addr, "pingCount()(uint256)", "--rpc-url", env["RPC_BASE_SEPOLIA"]]).decode().strip()
reactions = subprocess.check_output([cast, "call", addr, "reactionsCount()(uint256)", "--rpc-url", env["RPC_REACTIVE_LASNA"]]).decode().strip()
pongs = subprocess.check_output([cast, "call", addr, "pongCount()(uint256)", "--rpc-url", env["RPC_UNICHAIN_SEPOLIA"]]).decode().strip()

print(f"Base Sepolia pingCount: {pings}")
print(f"Reactive Lasna reactionsCount: {reactions}")
print(f"Unichain Sepolia pongCount: {pongs}")
