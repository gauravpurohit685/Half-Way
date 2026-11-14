import sqlite3

con = sqlite3.connect('data/halfway.db')
cur = con.cursor()
print('Checkpoints:', cur.execute('SELECT * FROM checkpoints').fetchall())
print('Events count:', cur.execute('SELECT count(*) FROM events').fetchone()[0])
print('Pools count:', cur.execute('SELECT count(*) FROM pools').fetchone()[0])
print('Opportunities count:', cur.execute('SELECT count(*) FROM opportunities').fetchone()[0])
opps = cur.execute('SELECT id, status, originChainId, destChainId FROM opportunities LIMIT 5').fetchall()
print('Sample Opportunities:', opps)
