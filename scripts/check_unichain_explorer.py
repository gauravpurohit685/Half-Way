import urllib.request
import json

url = "https://unichain-sepolia.blockscout.com/api?module=account&action=txlist&address=0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4&sort=desc"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print("Unichain Blockscout status:", data.get("status"), data.get("message"))
        txs = data.get("result", [])
        print(f"Total transactions found on Unichain proxy: {len(txs)}")
        for tx in txs[:5]:
            print(f"Tx: {tx.get('hash')} | From: {tx.get('from')} | Block: {tx.get('blockNumber')} | Time: {tx.get('timeStamp')}")
except Exception as e:
    print("Error querying Unichain Blockscout:", e)
