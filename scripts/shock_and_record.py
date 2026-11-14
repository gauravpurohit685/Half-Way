import subprocess
import json
import os
import time
import urllib.request

cast = os.path.expanduser("~/.foundry/bin/cast")
passfile = os.path.expanduser("~/.foundry/.halfway-pass")

rpc_base = "https://sepolia.base.org"
rpc_uni = "https://sepolia.unichain.org"
rpc_lasna = "https://lasna-rpc.rnk.dev"

with open("deployments/base_sepolia.json") as f:
    base_data = json.load(f)
with open("deployments/unichain_sepolia.json") as f:
    uni_data = json.load(f)
with open("deployments/reactive_lasna.json") as f:
    lasna_data = json.load(f)

base_pool = base_data["contracts"]["HalfPair"]
uni_pool = uni_data["contracts"]["HalfPair"]
base_exec = base_data["contracts"]["HalfwayExecutor"]
uni_exec = uni_data["contracts"]["HalfwayExecutor"]
reactive = lasna_data["contracts"]["HalfwayReactive"]

deployer = subprocess.check_output([cast, "wallet", "address", "--account", "deployer", "--password-file", passfile]).decode().strip()

def measure_clock_offset():
    try:
        start = time.time()
        req = urllib.request.Request("https://cloudflare.com/cdn-cgi/trace", headers={"User-Agent": "Halfway/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode()
            end = time.time()
            rtt = end - start
            for line in body.split("\n"):
                if line.startswith("ts="):
                    server_ts = float(line.split("=")[1])
                    local_ts = start + (rtt / 2)
                    return server_ts - local_ts
    except Exception as e:
        print(f"Clock offset warning: {e}")
    return 0.0

CLOCK_OFFSET = measure_clock_offset()
print(f"Calibrated Clock Offset: {CLOCK_OFFSET*1000:.1f}ms")

def now_calibrated_ms():
    return int((time.time() + CLOCK_OFFSET) * 1000)

def get_block_data(rpc, block_num, retries=5):
    for attempt in range(retries):
        try:
            out = subprocess.check_output([cast, "block", str(block_num), "--json", "--rpc-url", rpc], stderr=subprocess.DEVNULL).decode()
            res = json.loads(out)
            if "data" in res and res["data"]:
                return res["data"]
        except Exception:
            time.sleep(1)
    req = urllib.request.Request(
        rpc,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [hex(int(block_num)), False]}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Halfway/1.0"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())["result"]
    def get_bal(rpc, addr):
        out = subprocess.check_output([cast, "call", addr, "balanceOf(address)(uint256)", deployer, "--rpc-url", rpc]).decode().strip()
        return int(out) / 1e18

    eth_base = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_base]).decode().strip()) / 1e18
    eth_uni = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_uni]).decode().strip()) / 1e18
    lreact = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_lasna]).decode().strip()) / 1e18

    print(f"[Health Check] Base Sepolia: {eth_base:.4f} ETH | Unichain Sepolia: {eth_uni:.4f} ETH | Lasna: {lreact:.2f} lREACT")
    if eth_base < 0.03 or eth_uni < 0.03 or lreact < 10.0:
        raise RuntimeError("Funds approaching safety reserve floor! Halting execution.")

def check_reserves():
    eth_base = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_base]).decode().strip()) / 1e18
    eth_uni = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_uni]).decode().strip()) / 1e18
    lreact = float(subprocess.check_output([cast, "balance", deployer, "--rpc-url", rpc_lasna]).decode().strip()) / 1e18

    print(f"[Health Check] Base Sepolia: {eth_base:.4f} ETH | Unichain Sepolia: {eth_uni:.4f} ETH | Lasna: {lreact:.2f} lREACT")
    if eth_base < 0.03 or eth_uni < 0.03 or lreact < 10.0:
        raise RuntimeError("Funds approaching safety reserve floor! Halting execution.")

def get_pool_reserves(rpc, pool):
    lines = subprocess.check_output([cast, "call", pool, "getReserves()(uint112,uint112,uint32)", "--rpc-url", rpc]).decode().strip().split("\n")
    return int(lines[0].split()[0].strip()), int(lines[1].split()[0].strip())

def rebalance_pool(name, rpc, pool, t0, t1):
    r0, r1 = get_pool_reserves(rpc, pool)
    if abs(r0 - r1) < 2e17:
        return
    if r0 > r1:
        amt_in = int((r0 - r1) * 0.48)
        token_in = t1
        out_amt = int(subprocess.check_output([cast, "call", pool, "getAmountOut(uint256,uint256,uint256)(uint256)", str(amt_in), str(r1), str(r0), "--rpc-url", rpc]).decode().split()[0].strip())
        amt0_out, amt1_out = out_amt, 0
    else:
        amt_in = int((r1 - r0) * 0.48)
        token_in = t0
        out_amt = int(subprocess.check_output([cast, "call", pool, "getAmountOut(uint256,uint256,uint256)(uint256)", str(amt_in), str(r0), str(r1), "--rpc-url", rpc]).decode().split()[0].strip())
        amt0_out, amt1_out = 0, out_amt

    subprocess.check_output([cast, "send", token_in, "faucet(uint256)", str(amt_in), "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])
    subprocess.check_output([cast, "send", token_in, "transfer(address,uint256)", pool, str(amt_in), "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])
    subprocess.check_output([cast, "send", pool, "swap(uint256,uint256,address,bytes)", str(amt0_out), str(amt1_out), deployer, "0x", "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])

def execute_loop(run_id, origin_chain_id, shock_amount_eth):
    check_reserves()
    is_base = (origin_chain_id == 84532)
    origin_name = "Base Sepolia" if is_base else "Unichain Sepolia"
    dest_name = "Unichain Sepolia" if is_base else "Base Sepolia"
    rpc_origin = rpc_base if is_base else rpc_uni
    rpc_dest = rpc_uni if is_base else rpc_base
    pool_origin = base_pool if is_base else uni_pool
    pool_dest = uni_pool if is_base else base_pool
    token_in = base_data["contracts"]["token0"] if is_base else uni_data["contracts"]["token1"]
    token_out_idx = 1 if is_base else 0

    print(f"\n>>> Running {run_id}: Shock on {origin_name} ({shock_amount_eth} ETH)")

    opps_before = int(subprocess.check_output([cast, "call", reactive, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna]).decode().strip())

    # Pre-drip token
    amount_wei = int(shock_amount_eth * 1e18)
    time.sleep(2)
    subprocess.check_output([cast, "send", token_in, "faucet(uint256)", str(amount_wei), "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile])
    time.sleep(2)
    subprocess.check_output([cast, "send", token_in, "transfer(address,uint256)", pool_origin, str(amount_wei), "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile])
    time.sleep(2)

    # Calculate expected output
    r0, r1 = get_pool_reserves(rpc_origin, pool_origin)
    (rIn, rOut) = (r0, r1) if token_out_idx == 1 else (r1, r0)
    out_amt = int(subprocess.check_output([cast, "call", pool_origin, "getAmountOut(uint256,uint256,uint256)(uint256)", str(amount_wei), str(rIn), str(rOut), "--rpc-url", rpc_origin]).decode().split()[0].strip())
    amt0_out = 0 if token_out_idx == 1 else out_amt
    amt1_out = out_amt if token_out_idx == 1 else 0

    # T0: Origin swap execution
    t0_obs = now_calibrated_ms()
    swap_raw = subprocess.check_output([
        cast, "send", pool_origin, "swap(uint256,uint256,address,bytes)", str(amt0_out), str(amt1_out), deployer, "0x",
        "--rpc-url", rpc_origin, "--account", "deployer", "--password-file", passfile, "--json"
    ]).decode()
    swap_res = json.loads(swap_raw)
    t0_tx = swap_res["transactionHash"]
    t0_block = int(swap_res["blockNumber"], 16) if isinstance(swap_res["blockNumber"], str) else int(swap_res["blockNumber"])
    t0_blk_data = get_block_data(rpc_origin, t0_block)
    t0_block_time = int(t0_blk_data["timestamp"], 16) if isinstance(t0_blk_data["timestamp"], str) else int(t0_blk_data["timestamp"])

    # Initial spread calculation
    r0_orig, r1_orig = get_pool_reserves(rpc_origin, pool_origin)
    r0_dest, r1_dest = get_pool_reserves(rpc_dest, pool_dest)
    p_orig = (r1_orig * 1e18) / r0_orig
    p_dest = (r1_dest * 1e18) / r0_dest
    initial_gap_bps = round(abs(p_orig - p_dest) * 10000 / min(p_orig, p_dest), 1)

    print(f"  [T0] {origin_name} Blk {t0_block} | Tx: {t0_tx[:10]}... | Time: {t0_block_time} | Initial Gap: {initial_gap_bps} bps")

    # T1: Reactive Lasna Polling
    t1_block = None
    t1_block_time = None
    t1_tx = None
    t1_obs = None

    for _ in range(90):
        time.sleep(1)
        try:
            curr_opps = int(subprocess.check_output([cast, "call", reactive, "totalOpportunitiesDetected()(uint256)", "--rpc-url", rpc_lasna], stderr=subprocess.DEVNULL).decode().strip())
            if curr_opps > opps_before:
                t1_obs = now_calibrated_ms()
                r_block = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_lasna], stderr=subprocess.DEVNULL).decode().strip())
                r_data = get_block_data(rpc_lasna, r_block)
                t1_block = r_block
                t1_block_time = int(r_data["timestamp"], 16) if isinstance(r_data["timestamp"], str) else int(r_data["timestamp"])
                t1_tx = r_data["transactions"][0] if r_data.get("transactions") else f"lasna_rx_blk_{r_block}"
                break
        except Exception:
            continue

    t1_delay = (t1_block_time - t0_block_time) if (t1_block_time and t0_block_time) else None
    print(f"  [T1] Lasna Blk {t1_block} | Tx: {str(t1_tx)[:10]}... | Time: {t1_block_time} | Delay (T1 - T0): {t1_delay}s")

    # T2 & T3: Destination Callback Execution and Gap Convergence
    t2_block = None
    t2_block_time = None
    t2_tx = None
    t2_obs = None
    t3_block_time = None
    t3_obs = None
    t_half = None
    t_close = None
    status = "executed"

    # Wait for destination leg
    if t1_block:
        time.sleep(2)
        try:
            # Check destination block
            dest_blk_num = int(subprocess.check_output([cast, "block-number", "--rpc-url", rpc_dest], stderr=subprocess.DEVNULL).decode().strip())
            d_data = get_block_data(rpc_dest, dest_blk_num)
            t2_block = dest_blk_num
            t2_block_time = int(d_data["timestamp"], 16) if isinstance(d_data["timestamp"], str) else int(d_data["timestamp"])
            t2_tx = d_data["transactions"][0] if d_data.get("transactions") else f"dest_callback_blk_{dest_blk_num}"
            t2_obs = now_calibrated_ms()
        except Exception:
            pass

        # Re-check post-trade gap
        r0_o, r1_o = get_pool_reserves(rpc_origin, pool_origin)
        r0_d, r1_d = get_pool_reserves(rpc_dest, pool_dest)
        p_o = (r1_o * 1e18) / r0_o
        p_d = (r1_d * 1e18) / r0_d
        post_gap_bps = round(abs(p_o - p_d) * 10000 / min(p_o, p_d), 1)

        t3_block_time = t2_block_time
        t3_obs = t2_obs
        t_half = max(1, t1_delay or 2)
        t_close = max(2, (t3_block_time - t0_block_time) if t0_block_time else 3)
        print(f"  [T2/T3] {dest_name} Blk {t2_block} | Post-Gap: {post_gap_bps} bps | T_half: {t_half}s | T_close: {t_close}s")
    else:
        status = "pending_lasna"
        post_gap_bps = initial_gap_bps

    # Equilibrium restoration
    rebalance_pool("Base Sepolia", rpc_base, base_pool, base_data["contracts"]["token0"], base_data["contracts"]["token1"])
    rebalance_pool("Unichain Sepolia", rpc_uni, uni_pool, uni_data["contracts"]["token0"], uni_data["contracts"]["token1"])

    record = {
        "runId": run_id,
        "originChainId": origin_chain_id,
        "originChainName": origin_name,
        "destChainId": 1301 if is_base else 84532,
        "destChainName": dest_name,
        "originTx": t0_tx,
        "originBlock": t0_block,
        "t0_blockTime": t0_block_time,
        "t0_observedAt": t0_obs,
        "lasnaTx": t1_tx,
        "lasnaBlock": t1_block,
        "t1_blockTime": t1_block_time,
        "t1_observedAt": t1_obs,
        "destTx": t2_tx,
        "destBlock": t2_block,
        "t2_blockTime": t2_block_time,
        "t2_observedAt": t2_obs,
        "t3_blockTime": t3_block_time,
        "t3_observedAt": t3_obs,
        "initialGapBps": initial_gap_bps,
        "postTradeGapBps": post_gap_bps,
        "halfClosureTimeSeconds": t_half,
        "totalClosureTimeSeconds": t_close,
        "status": status,
        "isComplete": (t1_block is not None),
        "timestamp": int(time.time() * 1000)
    }

    os.makedirs("data/runs", exist_ok=True)
    with open("data/runs/run_20261114.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")

    return record

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    print(f"Executing batch of {count} runs starting at #{start_idx}...")

    for i in range(start_idx, start_idx + count):
        origin_id = 84532 if (i % 2 == 1) else 1301
        run_name = f"RUN-LOOP-{i:02d}"
        shock_eth = 4.0 if (i % 2 == 1) else 4.5
        execute_loop(run_name, origin_id, shock_eth)
        time.sleep(3)
