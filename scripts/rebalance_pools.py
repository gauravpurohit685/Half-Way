import subprocess
import json
import os
import time

cast = os.path.expanduser("~/.foundry/bin/cast")
passfile = os.path.expanduser("~/.foundry/.halfway-pass")

rpc_base = "https://sepolia.base.org"
rpc_uni = "https://sepolia.unichain.org"

with open("deployments/base_sepolia.json") as f:
    base_data = json.load(f)
with open("deployments/unichain_sepolia.json") as f:
    uni_data = json.load(f)

base_pool = base_data["contracts"]["HalfPair"]
uni_pool = uni_data["contracts"]["HalfPair"]
deployer = subprocess.check_output([cast, "wallet", "address", "--account", "deployer", "--password-file", passfile]).decode().strip()

def get_reserves(rpc, pool):
    lines = subprocess.check_output([cast, "call", pool, "getReserves()(uint112,uint112,uint32)", "--rpc-url", rpc]).decode().strip().split("\n")
    r0 = int(lines[0].split()[0].strip())
    r1 = int(lines[1].split()[0].strip())
    return r0, r1

def restore_pool(name, rpc, pool, t0, t1):
    r0, r1 = get_reserves(rpc, pool)
    print(f"[{name}] Reserves before: r0={r0/1e18:.3f}, r1={r1/1e18:.3f}")
    if abs(r0 - r1) < 1e17:
        print(f"[{name}] Already balanced.")
        return

    # If r0 > r1, swap t1 in to increase r1 and decrease r0
    if r0 > r1:
        # We need roughly sqrt(r0 * r1) for both. Target is ~ sqrt(r0 * r1)
        # Or simple swap of delta/2
        amt_in = int((r0 - r1) * 0.48)
        token_in = t1
        out_amt = int(subprocess.check_output([cast, "call", pool, "getAmountOut(uint256,uint256,uint256)(uint256)", str(amt_in), str(r1), str(r0), "--rpc-url", rpc]).decode().split()[0].strip())
        amt0_out, amt1_out = out_amt, 0
    else:
        amt_in = int((r1 - r0) * 0.48)
        token_in = t0
        out_amt = int(subprocess.check_output([cast, "call", pool, "getAmountOut(uint256,uint256,uint256)(uint256)", str(amt_in), str(r0), str(r1), "--rpc-url", rpc]).decode().split()[0].strip())
        amt0_out, amt1_out = 0, out_amt

    print(f"[{name}] Rebalancing: swapping {amt_in/1e18:.3f} tokens...")
    subprocess.check_output([cast, "send", token_in, "faucet(uint256)", str(amt_in), "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])
    subprocess.check_output([cast, "send", token_in, "transfer(address,uint256)", pool, str(amt_in), "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])
    subprocess.check_output([cast, "send", pool, "swap(uint256,uint256,address,bytes)", str(amt0_out), str(amt1_out), deployer, "0x", "--rpc-url", rpc, "--account", "deployer", "--password-file", passfile])

    r0_after, r1_after = get_reserves(rpc, pool)
    print(f"[{name}] Reserves after: r0={r0_after/1e18:.3f}, r1={r1_after/1e18:.3f}")

restore_pool("Base Sepolia", rpc_base, base_pool, base_data["contracts"]["token0"], base_data["contracts"]["token1"])
restore_pool("Unichain Sepolia", rpc_uni, uni_pool, uni_data["contracts"]["token0"], uni_data["contracts"]["token1"])
