import urllib.request
import json

url = "https://unichain-sepolia.blockscout.com/api?module=account&action=txlist&address=0x9299472A6399Fd1027ebF067571Eb3e3D7837FC4&page=1&offset=10&sort=desc"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        txs = data.get("result", [])
        print(f"Transactions found: {len(txs)}")
        for tx in txs:
            print(f"Tx: {tx.get('hash')} | From: {tx.get('from')} | Block: {tx.get('blockNumber')} | Time: {tx.get('timeStamp')} | IsError: {tx.get('isError')}")
except Exception as e:
    print("Error:", e)
