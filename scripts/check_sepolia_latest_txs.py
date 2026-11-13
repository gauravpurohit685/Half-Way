import urllib.request
import json

url = "https://eth-sepolia.blockscout.com/api?module=account&action=txlist&address=0xc9f36411C9897e7F959D99ffca2a0Ba7ee0D7bDA&page=1&offset=5&sort=desc"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        txs = data.get("result", [])
        print(f"Latest 5 Sepolia proxy txs:")
        for tx in txs:
            print(f"Tx: {tx.get('hash')} | From: {tx.get('from')} | Block: {tx.get('blockNumber')} | Time: {tx.get('timeStamp')} | IsError: {tx.get('isError')}")
except Exception as e:
    print("Error:", e)
