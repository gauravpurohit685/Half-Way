import subprocess
import os

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

rpc_lasna = env.get("RPC_REACTIVE_LASNA", "").strip().strip("\"'").strip()
cast_bin = "/home/gaurav/.foundry/bin/cast"

sys_addr = "0x8888888888888888888888888888888888888888"
res = subprocess.run([cast_bin, "code", sys_addr, "--rpc-url", rpc_lasna], capture_output=True, text=True)
print("Lasna System contract code length:", len(res.stdout.strip()))

old_sys_addr = "0x0000000000000000000000000000000000fffFfF"
res2 = subprocess.run([cast_bin, "code", old_sys_addr, "--rpc-url", rpc_lasna], capture_output=True, text=True)
print("Legacy System contract code length:", len(res2.stdout.strip()))
