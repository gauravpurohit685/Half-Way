import subprocess
import json

cast_bin = "/home/gaurav/.foundry/bin/cast"
rpc = "https://lasna-rpc.rnk.dev"

latest_res = json.loads(subprocess.check_output([cast_bin, "block", "latest", "--json", "--rpc-url", rpc]).decode())
latest_num = int(latest_res["data"]["number"], 16)
print(f"Latest Lasna block: {latest_num}")

timestamps = []
count = 15
for b in range(latest_num - count, latest_num + 1):
    res = subprocess.check_output([cast_bin, "block", str(b), "--json", "--rpc-url", rpc]).decode()
    b_data = json.loads(res)["data"]
    ts = int(b_data["timestamp"], 16)
    timestamps.append((b, ts))

diffs = [timestamps[i+1][1] - timestamps[i][1] for i in range(len(timestamps)-1)]
avg_block_time = sum(diffs) / len(diffs)
print(f"Consecutive timestamp differences (seconds): {diffs}")
print(f"Average Lasna block time: {avg_block_time:.2f} s")
