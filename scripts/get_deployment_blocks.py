import json

for path, name in [
    ("broadcast/DeployHalfwayL2.s.sol/84532/run-latest.json", "Base Sepolia"),
    ("broadcast/DeployHalfwayL2.s.sol/1301/run-latest.json", "Unichain Sepolia"),
    ("broadcast/DeployHalfwayReactive.s.sol/5318007/run-latest.json", "Reactive Lasna"),
]:
    with open(path) as f:
        d = json.load(f)
        receipts = d.get("receipts", [])
        if receipts:
            blocks = [int(r.get("blockNumber", "0x0"), 16) for r in receipts]
            print(f"{name} Start Block: {min(blocks)}")
        else:
            txs = d.get("transactions", [])
            print(f"{name} has {len(txs)} txs")
            if txs:
                print("First tx keys:", list(txs[0].keys()))
