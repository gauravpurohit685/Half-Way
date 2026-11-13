import subprocess
import json
import time

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

cast = "/home/gaurav/.foundry/bin/cast"
passfile = "/home/gaurav/.foundry/.halfway-pass"

origin_addr = "0xc471090292e60580625fb0b796199f253c3d8f90"
reactive_addr = "0x644b88b9081968d5f72f02f467d4d7d22a5d44d5"
dest_addr = "0x3f6bfb643f9d4b2a03062333344abd80644d33ae"

rpc_base = env["RPC_BASE_SEPOLIA"]
rpc_lasna = env["RPC_REACTIVE_LASNA"]
rpc_sepolia = env["RPC_SEPOLIA"]

print("=== STARTING HELLO-LOOP V2 TEST ===")
init_reactions = int(subprocess.check_output([cast, "call", reactive_addr, "reactionsCount()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
init_pongs = int(subprocess.check_output([cast, "call", dest_addr, "pongCount()(uint256)", "--rpc-url", rpc_sepolia]).decode().strip())
print(f"Initial state: Lasna reactions={init_reactions}, Sepolia pongs={init_pongs}")

print("\n--- HOP 1: Firing Ping on Base Sepolia ---")
wall_start = time.time()
send_res = subprocess.check_output([
    cast, "send", origin_addr, "ping(uint256)", "3003",
    "--rpc-url", rpc_base,
    "--account", "deployer",
    "--password-file", passfile,
    "--json"
]).decode()

send_data = json.loads(send_res)
t0_hash = send_data["transactionHash"]
t0_block_hex = send_data["blockNumber"]
t0_block = int(t0_block_hex, 16) if isinstance(t0_block_hex, str) and t0_block_hex.startswith("0x") else int(t0_block_hex)

b_res = json.loads(subprocess.check_output([cast, "block", str(t0_block), "--json", "--rpc-url", rpc_base]).decode())
t0_time = int(b_res["data"]["timestamp"], 16)
print(f"Origin Ping confirmed! Tx: {t0_hash} | Block: {t0_block} | Timestamp (T0): {t0_time}")

print("\n--- HOP 2: Waiting for Reactive Lasna reaction ---")
t1_hash = None
t1_block = None
t1_time = None
start_lasna = time.time()

while time.time() - start_lasna < 60:
    time.sleep(1)
    curr_reactions = int(subprocess.check_output([cast, "call", reactive_addr, "reactionsCount()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
    if curr_reactions > init_reactions:
        elapsed = time.time() - wall_start
        print(f"Reaction detected on Lasna! reactionsCount={curr_reactions} (+{elapsed:.2f}s)")
        r_block = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_lasna]).decode().strip())
        r_b_data = json.loads(subprocess.check_output([cast, "block", str(r_block), "--json", "--rpc-url", rpc_lasna]).decode())["data"]
        t1_block = r_block
        t1_time = int(r_b_data["timestamp"], 16)
        t1_hash = r_b_data["transactions"][0] if r_b_data["transactions"] else "reactive_system_tx"
        print(f"Lasna reaction block: {t1_block} | Timestamp (T1): {t1_time}")
        break

print("\n--- HOP 3: Waiting for Destination callback on Ethereum Sepolia ---")
t2_time = None
t2_block = None
start_dest = time.time()
wall_end = None

while time.time() - start_dest < 180:
    time.sleep(2)
    curr_pongs = int(subprocess.check_output([cast, "call", dest_addr, "pongCount()(uint256)", "--rpc-url", rpc_sepolia]).decode().strip())
    if curr_pongs > init_pongs:
        wall_end = time.time()
        elapsed = wall_end - wall_start
        print(f"PONG CALLBACK CONFIRMED on Sepolia! pongCount={curr_pongs} (+{elapsed:.2f}s)")
        t2_time = int(subprocess.check_output([cast, "call", dest_addr, "receivedPings(uint256)(uint256)", "2", "--rpc-url", rpc_sepolia]).decode().strip())
        d_block = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_sepolia]).decode().strip())
        t2_block = d_block
        print(f"Sepolia arrival block: {t2_block} | Timestamp (T2): {t2_time}")
        break

print("\n===============================")
print("=== HELLO-LOOP RUN SUMMARY ===")
print("===============================")
print(f"Hop 1 (Origin Base Sepolia): Tx {t0_hash} | Block {t0_block} | T0 = {t0_time}")
print(f"Hop 2 (Reactive Lasna):     Block {t1_block} | T1 = {t1_time}")
if t1_time and t0_time:
    print(f"  -> Reactive Processing (T1 - T0): {t1_time - t0_time}s")
print(f"Hop 3 (Destination Sepolia): Block {t2_block} | T2 = {t2_time}")
if t2_time and t0_time:
    print(f"  -> Total On-Chain Latency (T2 - T0): {t2_time - t0_time}s")
if wall_end:
    print(f"  -> Observer Wall-Clock Latency: {wall_end - wall_start:.2f}s")
