import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

cast_bin = "/home/gaurav/.foundry/bin/cast"
rpc_base = env.get("RPC_BASE_SEPOLIA", "").strip().strip("\"'").strip()
rpc_uni = env.get("RPC_UNICHAIN_SEPOLIA", "").strip().strip("\"'").strip()

# Base Sepolia Factory
base_v3_factory = "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"
code_base = subprocess.check_output([cast_bin, "code", base_v3_factory, "--rpc-url", rpc_base]).decode().strip()
print(f"Base Sepolia UniswapV3Factory code length: {len(code_base)}")

# Unichain Sepolia Factory
uni_v3_factory = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
code_uni = subprocess.check_output([cast_bin, "code", uni_v3_factory, "--rpc-url", rpc_uni]).decode().strip()
print(f"Unichain Sepolia UniswapV3Factory code length: {len(code_uni)}")
