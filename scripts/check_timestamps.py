import urllib.request
import json
import os

rpcs = {
    'Base Sepolia': 'https://sepolia.base.org',
    'Unichain Sepolia': 'https://sepolia.unichain.org',
    'Reactive Lasna': 'https://lasna-rpc.rnk.dev'
}

def rpc_call(url, method, params):
    req = urllib.request.Request(
        url,
        data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Halfway/1.0'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))['result']

for name, url in rpcs.items():
    print(f'=== {name} ===')
    latest_hex = rpc_call(url, 'eth_blockNumber', [])
    latest = int(latest_hex, 16)
    print(f'Latest block: {latest}')
    
    blocks = []
    for b in range(latest - 4, latest + 1):
        blk = rpc_call(url, 'eth_getBlockByNumber', [hex(b), False])
        ts = int(blk['timestamp'], 16)
        blocks.append((b, ts, blk))
    
    for i in range(len(blocks)):
        b, ts, blk = blocks[i]
        diff = ts - blocks[i-1][1] if i > 0 else 0
        hex_ts = blk.get("timestamp")
        print(f'Block {b}: timestamp={ts} ({hex_ts}), delta={diff}s')
    
    sample = blocks[-1][2]
    extra_fields = [k for k in sample.keys() if 'time' in k.lower() or 'nano' in k.lower() or 'micro' in k.lower()]
    print(f'Timestamp-related keys in header: {extra_fields}')
    print('All keys in block header:', sorted(list(sample.keys())))
    print()
