import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
rec = "0x644b88b9081968d5f72f02f467d4d7d22a5d44d5"
dest = "0x3f6bfb643f9d4b2a03062333344abd80644d33ae"

reactions = subprocess.check_output([cast, "call", rec, "reactionsCount()(uint256)", "--rpc-url", env["RPC_REACTIVE_LASNA"]]).decode().strip()
pongs = subprocess.check_output([cast, "call", dest, "pongCount()(uint256)", "--rpc-url", env["RPC_SEPOLIA"]]).decode().strip()

print(f"Lasna reactionsCount: {reactions}")
print(f"Sepolia pongCount: {pongs}")
