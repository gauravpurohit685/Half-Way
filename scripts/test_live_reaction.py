import subprocess
import json
import time

cast = "/home/gaurav/.foundry/bin/cast"
passfile = "/home/gaurav/.foundry/.halfway-pass"
rpc_base = "https://sepolia.base.org"
rpc_lasna = "https://lasna-rpc.rnk.dev"

with open("deployments/base_sepolia.json") as f:
    base_pool = json.load(f)["contracts"]["HalfPair"]
with open("deployments/reactive_lasna.json") as f:
    reactive = json.load(f)["contracts"]["HalfwayReactive"]

deployer = subprocess.check_output([cast, "wallet", "address", "--account", "deployer", "--password-file", passfile]).decode().strip()

print("=== FIRING TEST SHOCK ON BASE SEPOLIA ===")
t0 = subprocess.check_output([cast, "call", base_pool, "token0()(address)", "--rpc-url", rpc_base]).decode().strip()

opps_before = int(subprocess.check_output([cast, "call", reactive, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
print(f"Lasna totalOpportunitiesBefore: {opps_before}")

wall_start = time.time()

# 1. Drip 2 ether of token0 to pool
subprocess.check_output([cast, "send", t0, "faucet(uint256)", "2ether", "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile])
subprocess.check_output([cast, "send", t0, "transfer(address,uint256)", base_pool, "2ether", "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile])

# 2. Swap on pool
lines = subprocess.check_output([cast, "call", base_pool, "getReserves()(uint112,uint112,uint32)", "--rpc-url", rpc_base]).decode().strip().split("\n")
r0 = int(lines[0].split()[0].strip())
r1 = int(lines[1].split()[0].strip())
out = int(subprocess.check_output([cast, "call", base_pool, "getAmountOut(uint256,uint256,uint256)(uint256)", "2ether", str(r0), str(r1), "--rpc-url", rpc_base]).decode().split()[0].strip())

swap_res = json.loads(subprocess.check_output([
    cast, "send", base_pool, "swap(uint256,uint256,address,bytes)", "0", str(out), deployer, "0x",
    "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile, "--json"
]).decode())

t0_tx = swap_res["transactionHash"]
t0_block_hex = swap_res["blockNumber"]
t0_block = int(t0_block_hex, 16) if isinstance(t0_block_hex, str) and t0_block_hex.startswith("0x") else int(t0_block_hex)
b_data = json.loads(subprocess.check_output([cast, "block", str(t0_block), "--json", "--rpc-url", rpc_base]).decode())["data"]
t0_time = int(b_data["timestamp"], 16)

print(f"Hop 1 (Origin Swap Confirmed): Tx {t0_tx} | Block {t0_block} | T0 = {t0_time}")

print("Hop 2: Waiting for Reactive Lasna reaction...")
for i in range(60):
    time.sleep(1)
    opps_now = int(subprocess.check_output([cast, "call", reactive, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
    if opps_now > opps_before:
        wall_now = time.time()
        print(f"🎉 BOOM! Opportunity detected on Reactive Lasna! Count={opps_now} (+{wall_now - wall_start:.2f}s wall clock)")
        r_block = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_lasna]).decode().strip())
        r_data = json.loads(subprocess.check_output([cast, "block", str(r_block), "--json", "--rpc-url", rpc_lasna]).decode())["data"]
        t1_time = int(r_data["timestamp"], 16)
        print(f"Lasna Arrival Block: {r_block} | T1 = {t1_time} | Reactive Delay (T1 - T0): {t1_time - t0_time}s")
        break

print("Done test.")
