import sqlite3
import json
import os

db_path = 'data/halfway.db'
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    originChainId INTEGER NOT NULL,
    destChainId INTEGER NOT NULL,
    originTxHash TEXT,
    lasnaTxHash TEXT,
    destTxHash TEXT,
    t0_blockTime INTEGER,
    t0_observedAt INTEGER,
    t1_blockTime INTEGER,
    t1_observedAt INTEGER,
    t2_blockTime INTEGER,
    t2_observedAt INTEGER,
    t3_blockTime INTEGER,
    t3_observedAt INTEGER,
    halfClosureTimeSeconds REAL,
    totalClosureTimeSeconds REAL,
    initialGapBps REAL NOT NULL,
    postTradeGapBps REAL,
    status TEXT NOT NULL,
    isBuyToken0 INTEGER NOT NULL,
    amountIn TEXT NOT NULL,
    expectedOut TEXT,
    actualOut TEXT,
    pnlToken0 TEXT,
    pnlToken1 TEXT,
    failureReason TEXT,
    isComplete INTEGER NOT NULL,
    createdAt INTEGER NOT NULL
)
''')

inserted = 0
jsonl_path = 'data/runs/run_20261114.jsonl'
if os.path.exists(jsonl_path):
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            opp_id = r.get('runId')
            c.execute('''
            INSERT OR REPLACE INTO opportunities (
                id, originChainId, destChainId, originTxHash, lasnaTxHash, destTxHash,
                t0_blockTime, t0_observedAt, t1_blockTime, t1_observedAt, t2_blockTime, t2_observedAt,
                t3_blockTime, t3_observedAt, halfClosureTimeSeconds, totalClosureTimeSeconds,
                initialGapBps, postTradeGapBps, status, isBuyToken0, amountIn, expectedOut,
                actualOut, pnlToken0, pnlToken1, failureReason, isComplete, createdAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opp_id,
                r.get('originChainId', 0),
                r.get('destChainId', 0),
                (r.get('originTx') or '').lower() or None,
                (r.get('lasnaTx') or '').lower() or None,
                (r.get('destTx') or '').lower() or None,
                r.get('t0_blockTime'),
                r.get('t0_observedAt'),
                r.get('t1_blockTime'),
                r.get('t1_observedAt'),
                r.get('t2_blockTime'),
                r.get('t2_observedAt'),
                r.get('t3_blockTime'),
                r.get('t3_observedAt'),
                r.get('halfClosureTimeSeconds'),
                r.get('totalClosureTimeSeconds'),
                r.get('initialGapBps', 0.0),
                r.get('postTradeGapBps'),
                r.get('status', 'executed'),
                1 if r.get('originChainId') == 84532 else 0,
                '4000000000000000000',
                None, None, None, None,
                r.get('failureReason'),
                1 if r.get('isComplete') else 0,
                r.get('timestamp', 0)
            ))
            inserted += 1

conn.commit()
print(f"Successfully synced {inserted} records into {db_path}")

c.execute("SELECT COUNT(*), SUM(isComplete) FROM opportunities")
tot, comp = c.fetchone()
print(f"Database totals: {tot} opportunities ({comp} complete)")
