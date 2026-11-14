import subprocess
import json

cast = "/home/gaurav/.foundry/bin/cast"
lasna_rpc = "https://lasna-rpc.rnk.dev"
reactive = "0x61a66307fa18203110f73745628252592d975c9f"

with open("deployments/base_sepolia.json") as f:
    base_pool = json.load(f)["contracts"]["HalfPair"]
with open("deployments/unichain_sepolia.json") as f:
    uni_pool = json.load(f)["contracts"]["HalfPair"]

# uint256 is 32 bytes (64 hex chars), address is 20 bytes (40 hex chars)
cid_a_hex = f"{84532:064x}"
addr_a_hex = base_pool.lower().replace("0x", "").zfill(40)
keyA = subprocess.check_output([cast, "keccak", "0x" + cid_a_hex + addr_a_hex]).decode().strip()

cid_b_hex = f"{1301:064x}"
addr_b_hex = uni_pool.lower().replace("0x", "").zfill(40)
keyB = subprocess.check_output([cast, "keccak", "0x" + cid_b_hex + addr_b_hex]).decode().strip()

print("Base Pool:", base_pool, "Key:", keyA)
print("Uni Pool:", uni_pool, "Key:", keyB)

stateA = subprocess.check_output([cast, "call", reactive, "poolStates(bytes32)(uint112,uint112,uint32,uint256)", keyA, "--rpc-url", lasna_rpc]).decode()
stateB = subprocess.check_output([cast, "call", reactive, "poolStates(bytes32)(uint112,uint112,uint32,uint256)", keyB, "--rpc-url", lasna_rpc]).decode()

print("State A (Base):", stateA)
print("State B (Uni):", stateB)
