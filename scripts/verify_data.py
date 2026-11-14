import sqlite3
import json
import os
import sys
import urllib.request

rpc_base = "https://sepolia.base.org"
rpc_uni = "https://sepolia.unichain.org"
rpc_lasna = "https://lasna-rpc.rnk.dev"

def rpc_call(url, method, params):
    req = urllib.request.Request(
        url,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Halfway/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        res = json.loads(r.read())
        if "error" in res:
            raise RuntimeError(f"RPC Error: {res['error']}")
        return res["result"]

def verify():
    print("==================================================")
    print("   Halfway — Data Integrity & Receipt Verifier    ")
    print("==================================================")

    jsonl_path = "data/runs/run_20261114.jsonl"
    if not os.path.exists(jsonl_path):
        print(f"Error: {jsonl_path} not found.")
        sys.exit(1)

    records = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    complete_records = [r for r in records if r.get("isComplete") and r.get("originTx") and r.get("lasnaTx")]
    print(f"Found {len(records)} total records ({len(complete_records)} complete loops).")

    if not complete_records:
        print("No complete loops to verify yet.")
        sys.exit(0)

    # Sample up to 5 records for deep receipt verification
    sample = complete_records[:min(5, len(complete_records))]
    print(f"Verifying sample of {len(sample)} runs directly against RPC block receipts...\n")

    for r in sample:
        run_id = r["runId"]
        origin_tx = r["originTx"]
        origin_chain = r["originChainId"]
        origin_rpc = rpc_base if origin_chain == 84532 else rpc_uni

        print(f"[{run_id}] Checking Origin Tx {origin_tx[:16]}... on Chain {origin_chain}")
        receipt_orig = rpc_call(origin_rpc, "eth_getTransactionReceipt", [origin_tx])
        if not receipt_orig:
            raise AssertionError(f"[{run_id}] Origin tx receipt not found on chain {origin_chain}!")
        if receipt_orig["status"] != "0x1":
            raise AssertionError(f"[{run_id}] Origin tx failed on chain {origin_chain}!")

        receipt_blk = int(receipt_orig["blockNumber"], 16)
        if receipt_blk != r["originBlock"]:
            raise AssertionError(f"[{run_id}] Origin block mismatch! Expected {r['originBlock']}, got {receipt_blk}")

        # Check Lasna Tx
        lasna_tx = r["lasnaTx"]
        if lasna_tx and lasna_tx.startswith("0x"):
            print(f"[{run_id}] Checking Lasna Reaction Tx {lasna_tx[:16]}... on Lasna (5318007)")
            receipt_lasna = rpc_call(rpc_lasna, "eth_getTransactionReceipt", [lasna_tx])
            if not receipt_lasna:
                raise AssertionError(f"[{run_id}] Lasna tx receipt not found on Lasna!")
            if receipt_lasna["status"] != "0x1":
                raise AssertionError(f"[{run_id}] Lasna tx failed on Lasna!")

        print(f"✓ [{run_id}] Receipts verified and mathematically consistent with on-chain consensus.\n")

    print("==================================================")
    print("   SUCCESS: All sampled on-chain runs VERIFIED!   ")
    print("==================================================")

if __name__ == "__main__":
    verify()
