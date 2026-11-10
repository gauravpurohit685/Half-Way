import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

cast_bin = "/home/gaurav/.foundry/bin/cast"
rpc_base = env.get("RPC_BASE_SEPOLIA", "").strip().strip("\"'").strip()
rpc_uni = env.get("RPC_UNICHAIN_SEPOLIA", "").strip().strip("\"'").strip()

pools = [
    ("Base Sepolia (Fee 500)", rpc_base, "0x94bfc0574FF48E92cE43d495376C477B1d0EEeC0"),
    ("Base Sepolia (Fee 3000)", rpc_base, "0x46880b404CD35c165EDdefF7421019F8dD25F4Ad"),
    ("Unichain Sepolia (Fee 500)", rpc_uni, "0xBeAD5792bB6C299AB11Eaa425aC3fE11ebA47b3B"),
    ("Unichain Sepolia (Fee 3000)", rpc_uni, "0x8F463126bBEA80A10DF9Bf6FF5455B6B0292B34e"),
]

for label, rpc, pool in pools:
    try:
        liq = subprocess.check_output([cast_bin, "call", pool, "liquidity()(uint128)", "--rpc-url", rpc]).decode().strip()
        slot0 = subprocess.check_output([cast_bin, "call", pool, "slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)", "--rpc-url", rpc]).decode().strip()
        print(f"[{label}] Pool: {pool}")
        print(f"  Liquidity: {liq}")
        print(f"  Slot0: {slot0}")
    except Exception as e:
        print(f"[{label}] Error: {e}")
