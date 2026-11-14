import urllib.request
import json

def rpc_call(url, method, params):
    req = urllib.request.Request(
        url,
        data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Halfway/1.0'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))['result']

base_url = 'https://sepolia.base.org'
latest = int(rpc_call(base_url, 'eth_blockNumber', []), 16)
for b in range(latest - 3, latest + 1):
    blk = rpc_call(base_url, 'eth_getBlockByNumber', [hex(b), False])
    ts = int(blk['timestamp'], 16)
    ts_ms = blk.get('timestampMs')
    print(f"Base Sepolia Block {b}: ts={ts}, timestampMs={ts_ms} ({int(ts_ms, 16) if ts_ms else None})")

uni_url = 'https://sepolia.unichain.org'
latest_uni = int(rpc_call(uni_url, 'eth_blockNumber', []), 16)
for b in range(latest_uni - 3, latest_uni + 1):
    blk = rpc_call(uni_url, 'eth_getBlockByNumber', [hex(b), False])
    ts = int(blk['timestamp'], 16)
    print(f"Unichain Sepolia Block {b}: ts={ts}, extraData={blk.get('extraData')}")
