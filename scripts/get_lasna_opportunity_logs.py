import subprocess
import json

cast = "/home/gaurav/.foundry/bin/cast"
lasna_rpc = "https://lasna-rpc.rnk.dev"
reactive = "0x61a66307fa18203110f73745628252592d975c9f"

logs = json.loads(subprocess.check_output([
    cast, "logs",
    "--address", reactive,
    "--from-block", "8317100",
    "--to-block", "latest",
    "--json",
    "--rpc-url", lasna_rpc
]).decode())

print(f"Total Logs on Lasna: {len(logs)}")
for i, l in enumerate(logs):
    tx = l.get("transactionHash")
    blk = int(l.get("blockNumber", "0x0"), 16)
    topics = l.get("topics", [])
    data = l.get("data", "")
    print(f"\n--- Log #{i+1} ---")
    print(f"Tx: {tx} | Block: {blk}")
    print(f"Topic 0: {topics[0] if topics else None}")
    if len(topics) > 1:
        print(f"Opportunity ID (Topic 1): {topics[1]}")
