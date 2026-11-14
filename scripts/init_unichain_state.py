import subprocess
import json
import time

cast = "/home/gaurav/.foundry/bin/cast"
passfile = "/home/gaurav/.foundry/.halfway-pass"
rpc_uni = "https://sepolia.unichain.org"

with open("deployments/unichain_sepolia.json") as f:
    uni_data = json.load(f)

uni_pool = uni_data["contracts"]["HalfPair"]
t0 = subprocess.check_output([cast, "call", uni_pool, "token0()(address)", "--rpc-url", rpc_uni]).decode().strip()

print(f"Triggering touch on Unichain pool {uni_pool} to initialize State B...")
subprocess.check_output([cast, "send", t0, "faucet(uint256)", "0.1ether", "--rpc-url", rpc_uni, "--account", "deployer", "--password-file", passfile])
subprocess.check_output([cast, "send", t0, "transfer(address,uint256)", uni_pool, "0.1ether", "--rpc-url", rpc_uni, "--account", "deployer", "--password-file", passfile])

# Query reserves
lines = subprocess.check_output([cast, "call", uni_pool, "getReserves()(uint112,uint112,uint32)", "--rpc-url", rpc_uni]).decode().strip().split("\n")
r0 = int(lines[0].split()[0].strip())
r1 = int(lines[1].split()[0].strip())
out = int(subprocess.check_output([cast, "call", uni_pool, "getAmountOut(uint256,uint256,uint256)(uint256)", "0.1ether", str(r0), str(r1), "--rpc-url", rpc_uni]).decode().split()[0].strip())

deployer = subprocess.check_output([cast, "wallet", "address", "--account", "deployer", "--password-file", passfile]).decode().strip()
swap_tx = subprocess.check_output([cast, "send", uni_pool, "swap(uint256,uint256,address,bytes)", "0", str(out), deployer, "0x", "--rpc-url", rpc_uni, "--account", "deployer", "--password-file", passfile]).decode()
print("Unichain touch swap complete!")
