import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

cast_bin = "/home/gaurav/.foundry/bin/cast"

proxies = {
    "Sepolia": (env.get("RPC_SEPOLIA", "").strip().strip("\"'").strip(), "0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA"),
    "Base Sepolia": (env.get("RPC_BASE_SEPOLIA", "").strip().strip("\"'").strip(), "0xa6eA49Ed671B8a4dfCDd34E36b7a75Ac79B8A5a6"),
    "Unichain Sepolia": (env.get("RPC_UNICHAIN_SEPOLIA", "").strip().strip("\"'").strip(), "0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4")
}

for name, (rpc, addr) in proxies.items():
    res = subprocess.run([cast_bin, "code", addr, "--rpc-url", rpc], capture_output=True, text=True)
    code = res.stdout.strip()
    print(f"[{name}] Callback Proxy {addr}: code length {len(code)}")
