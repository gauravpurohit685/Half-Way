import subprocess
import os

cast_path = os.path.expanduser("~/.foundry/bin/cast")
base_pool = "0x781264ed18eb99763ec0a5be964fafcfb86e9017"
uni_pool = "0x3f6bfb643f9d4b2a03062333344abd80644d33ae"

t0_base = subprocess.check_output(f"{cast_path} call {base_pool} 'token0()(address)' --rpc-url https://sepolia.base.org", shell=True).decode().strip()
t1_base = subprocess.check_output(f"{cast_path} call {base_pool} 'token1()(address)' --rpc-url https://sepolia.base.org", shell=True).decode().strip()
print(f"Base Pool tokens: t0={t0_base}, t1={t1_base}")

t0_uni = subprocess.check_output(f"{cast_path} call {uni_pool} 'token0()(address)' --rpc-url https://sepolia.unichain.org", shell=True).decode().strip()
t1_uni = subprocess.check_output(f"{cast_path} call {uni_pool} 'token1()(address)' --rpc-url https://sepolia.unichain.org", shell=True).decode().strip()
print(f"Unichain Pool tokens: t0={t0_uni}, t1={t1_uni}")
