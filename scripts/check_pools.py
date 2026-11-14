import subprocess
import os

cast_path = os.path.expanduser("~/.foundry/bin/cast")

base_pool = "0x781264ed18eb99763ec0a5be964fafcfb86e9017"
uni_pool = "0x3f6bfb643f9d4b2a03062333344abd80644d33ae"

res_base = subprocess.check_output(f"{cast_path} call {base_pool} 'getReserves()(uint112,uint112,uint32)' --rpc-url https://sepolia.base.org", shell=True).decode()
print("Base Pool Reserves:\n", res_base.strip())

res_uni = subprocess.check_output(f"{cast_path} call {uni_pool} 'getReserves()(uint112,uint112,uint32)' --rpc-url https://sepolia.unichain.org", shell=True).decode()
print("Unichain Pool Reserves:\n", res_uni.strip())
