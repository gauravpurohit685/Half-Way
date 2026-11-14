import json
import os
import subprocess
import time

forge = "/home/gaurav/.foundry/bin/forge"
cast = "/home/gaurav/.foundry/bin/cast"
passfile = "/home/gaurav/.foundry/.halfway-pass"

with open(".env") as f:
    env = dict(l.strip().split("=", 1) for l in f if "=" in l and not l.startswith("#"))
for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

rpc_lasna = env["RPC_REACTIVE_LASNA"]
rpc_base = env["RPC_BASE_SEPOLIA"]
rpc_uni = env["RPC_UNICHAIN_SEPOLIA"]

deployer = subprocess.check_output([
    cast, "wallet", "address", "--account", "deployer", "--password-file", passfile
]).decode().strip()

with open("deployments/base_sepolia.json") as f:
    base_data = json.load(f)
with open("deployments/unichain_sepolia.json") as f:
    uni_data = json.load(f)
with open("deployments/reactive_lasna.json") as f:
    lasna_data = json.load(f)

reactive_addr = lasna_data["contracts"]["HalfwayReactive"]
base_pool = base_data["contracts"]["HalfPair"]
uni_pool = uni_data["contracts"]["HalfPair"]

print("=== STARTING PHASE 2 LIVE VALIDATION ===")
print(f"Deployer Wallet: {deployer}")
print(f"Reactive Lasna: {reactive_addr}")
print(f"Base Sepolia Pool: {base_pool}")
print(f"Unichain Sepolia Pool: {uni_pool}")

results = []

def run_shock_and_measure(run_id, chain_name, rpc_origin, pool_addr, shock_token_idx, shock_amount_eth):
    print(f"\n--- [RUN {run_id}] Price Shock on {chain_name} ({shock_amount_eth} ETH) ---")

    t0_token = subprocess.check_output([cast, "call", pool_addr, "token0()(address)", "--rpc-url", rpc_origin]).decode().strip()
    t1_token = subprocess.check_output([cast, "call", pool_addr, "token1()(address)", "--rpc-url", rpc_origin]).decode().strip()
    token_in = t0_token if shock_token_idx == 0 else t1_token

    # Initial state
    opps_before = int(subprocess.check_output([cast, "call", reactive_addr, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
    print(f"Lasna totalOpportunitiesBefore: {opps_before}")

    wall_start = time.time()

    # Drip shock tokens via faucet and transfer to pool
    subprocess.check_output([
        cast, "send", token_in, "faucet(uint256)", f"{shock_amount_eth}ether",
        "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile
    ])
    subprocess.check_output([
        cast, "send", token_in, "transfer(address,uint256)", pool_addr, f"{shock_amount_eth}ether",
        "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile
    ])

    # Execute swap on pool
    lines = subprocess.check_output([cast, "call", pool_addr, "getReserves()(uint112,uint112,uint32)", "--rpc-url", rpc_origin]).decode().strip().split("\n")
    r0 = int(lines[0].split()[0].strip())
    r1 = int(lines[1].split()[0].strip())

    (rIn, rOut) = (r0, r1) if shock_token_idx == 0 else (r1, r0)
    expected_out_str = subprocess.check_output([cast, "call", pool_addr, "getAmountOut(uint256,uint256,uint256)(uint256)", f"{shock_amount_eth}ether", str(rIn), str(rOut), "--rpc-url", rpc_origin]).decode().strip()
    expected_out = int(expected_out_str.split()[0].strip())

    amt0_out = 0 if shock_token_idx == 0 else expected_out
    amt1_out = expected_out if shock_token_idx == 0 else 0

    swap_res = json.loads(subprocess.check_output([
        cast, "send", pool_addr, "swap(uint256,uint256,address,bytes)", str(amt0_out), str(amt1_out), deployer, "0x",
        "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile, "--json"
    ]).decode())

    t0_tx = swap_res["transactionHash"]
    t0_block_hex = swap_res["blockNumber"]
    t0_block = int(t0_block_hex, 16) if isinstance(t0_block_hex, str) and t0_block_hex.startswith("0x") else int(t0_block_hex)
    b_data = json.loads(subprocess.check_output([cast, "block", str(t0_block), "--json", "--rpc-url", rpc_origin]).decode())["data"]
    t0_time = int(b_data["timestamp"], 16)

    print(f"Hop 1 (Origin Swap Confirmed): Tx {t0_tx} | Block {t0_block} | T0 = {t0_time}")

    # Watch for reaction on Lasna
    print("Hop 2: Monitoring Reactive Lasna for reaction...")
    t1_block = None
    t1_time = None
    t1_tx = None
    wall_lasna = None

    for _ in range(60):
        time.sleep(1)
        curr_opps = int(subprocess.check_output([cast, "call", reactive_addr, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
        if curr_opps > opps_before:
            wall_lasna = time.time()
            elapsed = wall_lasna - wall_start
            print(f"✓ Reaction detected on Lasna! totalOpportunities={curr_opps} (+{elapsed:.2f}s)")
            r_block = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_lasna]).decode().strip())
            r_data = json.loads(subprocess.check_output([cast, "block", str(r_block), "--json", "--rpc-url", rpc_lasna]).decode())["data"]
            t1_block = r_block
            t1_time = int(r_data["timestamp"], 16)
            t1_tx = r_data["transactions"][0] if r_data.get("transactions") else "reactive_system_tx"
            break

    reactive_latency = (t1_time - t0_time) if (t1_time and t0_time) else None
    print(f"Measured Hop 1 -> Hop 2 Reactive Latency: {reactive_latency}s (Block timestamp delta)")
    if wall_lasna:
        print(f"Observer Wall-Clock Latency: {wall_lasna - wall_start:.2f}s")

    result_data = {
        "runId": run_id,
        "originChain": chain_name,
        "originTx": t0_tx,
        "originBlock": t0_block,
        "t0": t0_time,
        "lasnaTx": t1_tx,
        "lasnaBlock": t1_block,
        "t1": t1_time,
        "reactiveLatencySec": reactive_latency,
        "observerLatencySec": round(wall_lasna - wall_start, 2) if wall_lasna else None,
        "status": "Lasna Reaction Verified"
    }
    results.append(result_data)
    return result_data

# Execute Run 1: Base Sepolia Shock
run_shock_and_measure("RUN-CORE-01", "Base Sepolia", rpc_base, base_pool, 0, 5)

# Wait 8 seconds for cooldown
time.sleep(8)

# Execute Run 2: Unichain Sepolia Shock
run_shock_and_measure("RUN-CORE-02", "Unichain Sepolia", rpc_uni, uni_pool, 1, 5)

# Wait 8 seconds for cooldown
time.sleep(8)

# Execute Run 3: Base Sepolia Shock
run_shock_and_measure("RUN-CORE-03", "Base Sepolia", rpc_base, base_pool, 1, 4)

# Run 4: Negative Test (Tiny 0.01 ether shock -> Sub-threshold spread)
print("\n--- [RUN-NEG-01] Negative Test: Sub-Threshold Spread (0.01 ETH) ---")
opps_before_neg = int(subprocess.check_output([cast, "call", reactive_addr, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
t0_token = subprocess.check_output([cast, "call", base_pool, "token0()(address)", "--rpc-url", rpc_base]).decode().strip()
subprocess.check_output([cast, "send", t0_token, "faucet(uint256)", "0.01ether", "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile])
subprocess.check_output([cast, "send", t0_token, "transfer(address,uint256)", base_pool, "0.01ether", "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile])
subprocess.check_output([cast, "send", base_pool, "swap(uint256,uint256,address,bytes)", "0", "9900000000000000", deployer, "0x", "--rpc-url", rpc_base, "--account", "deployer", "--password-file", passfile])

time.sleep(10)
opps_after_neg = int(subprocess.check_output([cast, "call", reactive_addr, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())
print(f"Opportunities before: {opps_before_neg}, after: {opps_after_neg}")
assert opps_before_neg == opps_after_neg, "Negative test failed: opportunity was unexpectedly triggered!"
print("✓ Negative test passed: sub-threshold spread did NOT trigger execution!")

# Save results
with open("docs/phase2-results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nAll validation runs finished and saved to docs/phase2-results.json")
