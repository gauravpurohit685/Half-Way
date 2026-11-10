import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

cast_bin = "/home/gaurav/.foundry/bin/cast"
rpc_base = env.get("RPC_BASE_SEPOLIA", "").strip().strip("\"'").strip()
rpc_uni = env.get("RPC_UNICHAIN_SEPOLIA", "").strip().strip("\"'").strip()

base_v3_factory = "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24"
uni_v3_factory = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

weth_base = "0x4200000000000000000000000000000000000006"
usdc_base = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

weth_uni = "0x4200000000000000000000000000000000000006"
usdc_uni = "0x31d0220469e10c4E71834a79b1f276d740d3768F"

fees = [500, 3000, 10000]

print("--- Base Sepolia WETH/USDC pools ---")
for fee in fees:
    res = subprocess.check_output([
        cast_bin, "call", base_v3_factory,
        "getPool(address,address,uint24)(address)",
        weth_base, usdc_base, str(fee),
        "--rpc-url", rpc_base
    ]).decode().strip()
    print(f"Fee {fee}: {res}")

print("\n--- Unichain Sepolia WETH/USDC pools ---")
for fee in fees:
    res = subprocess.check_output([
        cast_bin, "call", uni_v3_factory,
        "getPool(address,address,uint24)(address)",
        weth_uni, usdc_uni, str(fee),
        "--rpc-url", rpc_uni
    ]).decode().strip()
    print(f"Fee {fee}: {res}")
