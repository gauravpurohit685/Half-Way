import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';
import { OpportunityRecord, PoolState, VaultState } from './types.js';

export class DB {
  public db: Database.Database;

  constructor(dbPath: string) {
    const dir = path.dirname(dbPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('synchronous = NORMAL');
    this.init();
  }

  private init() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS checkpoints (
        chainId INTEGER PRIMARY KEY,
        lastBlockNumber INTEGER NOT NULL,
        lastUpdatedAt INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS pools (
        chainId INTEGER NOT NULL,
        address TEXT NOT NULL,
        token0 TEXT NOT NULL,
        token1 TEXT NOT NULL,
        reserve0 TEXT NOT NULL,
        reserve1 TEXT NOT NULL,
        normalizedPrice TEXT NOT NULL,
        lastBlockNumber INTEGER NOT NULL,
        lastBlockTimestamp INTEGER NOT NULL,
        lastObservedAt INTEGER NOT NULL,
        PRIMARY KEY (chainId, address)
      );

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
      );

      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chainId INTEGER NOT NULL,
        blockNumber INTEGER NOT NULL,
        txHash TEXT NOT NULL,
        logIndex INTEGER NOT NULL,
        eventName TEXT NOT NULL,
        contractAddress TEXT NOT NULL,
        dataJson TEXT NOT NULL,
        blockTime INTEGER NOT NULL,
        observedAt INTEGER NOT NULL,
        UNIQUE (chainId, txHash, logIndex)
      );

      CREATE TABLE IF NOT EXISTS vault_state (
        chainId INTEGER PRIMARY KEY,
        executorAddress TEXT NOT NULL,
        totalShares TEXT NOT NULL,
        reserve0 TEXT NOT NULL,
        reserve1 TEXT NOT NULL,
        isPaused INTEGER NOT NULL,
        consecutiveFailures INTEGER NOT NULL,
        lastUpdatedBlock INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS user_shares (
        walletAddress TEXT NOT NULL,
        chainId INTEGER NOT NULL,
        shares TEXT NOT NULL,
        updatedAt INTEGER NOT NULL,
        PRIMARY KEY (walletAddress, chainId)
      );

      CREATE TABLE IF NOT EXISTS system_health (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updatedAt INTEGER NOT NULL
      );
    `);
  }

  // Checkpoints
  public getCheckpoint(chainId: number): number | null {
    const row = this.db.prepare('SELECT lastBlockNumber FROM checkpoints WHERE chainId = ?').get(chainId) as { lastBlockNumber: number } | undefined;
    return row ? row.lastBlockNumber : null;
  }

  public setCheckpoint(chainId: number, blockNumber: number) {
    this.db.prepare(`
      INSERT INTO checkpoints (chainId, lastBlockNumber, lastUpdatedAt)
      VALUES (?, ?, ?)
      ON CONFLICT(chainId) DO UPDATE SET
        lastBlockNumber = excluded.lastBlockNumber,
        lastUpdatedAt = excluded.lastUpdatedAt
    `).run(chainId, blockNumber, Date.now());
  }

  // Pools
  public upsertPool(p: PoolState) {
    this.db.prepare(`
      INSERT INTO pools (
        chainId, address, token0, token1, reserve0, reserve1,
        normalizedPrice, lastBlockNumber, lastBlockTimestamp, lastObservedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(chainId, address) DO UPDATE SET
        reserve0 = excluded.reserve0,
        reserve1 = excluded.reserve1,
        normalizedPrice = excluded.normalizedPrice,
        lastBlockNumber = excluded.lastBlockNumber,
        lastBlockTimestamp = excluded.lastBlockTimestamp,
        lastObservedAt = excluded.lastObservedAt
    `).run(
      p.chainId, p.address.toLowerCase(), p.token0.toLowerCase(), p.token1.toLowerCase(),
      p.reserve0, p.reserve1, p.normalizedPrice, p.lastBlockNumber, p.lastBlockTimestamp, p.lastObservedAt
    );
  }

  public getPool(chainId: number, address: string): PoolState | null {
    const row = this.db.prepare('SELECT * FROM pools WHERE chainId = ? AND address = ?').get(chainId, address.toLowerCase()) as any;
    return row || null;
  }

  public getAllPools(): PoolState[] {
    return this.db.prepare('SELECT * FROM pools').all() as PoolState[];
  }

  // Events
  public insertEvent(e: {
    chainId: number;
    blockNumber: number;
    txHash: string;
    logIndex: number;
    eventName: string;
    contractAddress: string;
    dataJson: string;
    blockTime: number;
    observedAt: number;
  }): boolean {
    try {
      this.db.prepare(`
        INSERT INTO events (
          chainId, blockNumber, txHash, logIndex, eventName,
          contractAddress, dataJson, blockTime, observedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        e.chainId, e.blockNumber, e.txHash.toLowerCase(), e.logIndex, e.eventName,
        e.contractAddress.toLowerCase(), e.dataJson, e.blockTime, e.observedAt
      );
      return true;
    } catch (err: any) {
      if (err.message && err.message.includes('UNIQUE constraint failed')) {
        return false; // Idempotent skip
      }
      throw err;
    }
  }

  // Opportunities
  public upsertOpportunity(opp: Partial<OpportunityRecord> & { id: string }) {
    const existing = this.getOpportunity(opp.id);
    if (!existing) {
      this.db.prepare(`
        INSERT INTO opportunities (
          id, originChainId, destChainId, originTxHash, lasnaTxHash, destTxHash,
          t0_blockTime, t0_observedAt, t1_blockTime, t1_observedAt, t2_blockTime, t2_observedAt,
          t3_blockTime, t3_observedAt, halfClosureTimeSeconds, totalClosureTimeSeconds,
          initialGapBps, postTradeGapBps, status, isBuyToken0, amountIn, expectedOut,
          actualOut, pnlToken0, pnlToken1, failureReason, isComplete, createdAt
        ) VALUES (
          @id, @originChainId, @destChainId, @originTxHash, @lasnaTxHash, @destTxHash,
          @t0_blockTime, @t0_observedAt, @t1_blockTime, @t1_observedAt, @t2_blockTime, @t2_observedAt,
          @t3_blockTime, @t3_observedAt, @halfClosureTimeSeconds, @totalClosureTimeSeconds,
          @initialGapBps, @postTradeGapBps, @status, @isBuyToken0, @amountIn, @expectedOut,
          @actualOut, @pnlToken0, @pnlToken1, @failureReason, @isComplete, @createdAt
        )
      `).run({
        id: opp.id,
        originChainId: opp.originChainId || 0,
        destChainId: opp.destChainId || 0,
        originTxHash: opp.originTxHash?.toLowerCase() || null,
        lasnaTxHash: opp.lasnaTxHash?.toLowerCase() || null,
        destTxHash: opp.destTxHash?.toLowerCase() || null,
        t0_blockTime: opp.t0_blockTime ?? null,
        t0_observedAt: opp.t0_observedAt ?? null,
        t1_blockTime: opp.t1_blockTime ?? null,
        t1_observedAt: opp.t1_observedAt ?? null,
        t2_blockTime: opp.t2_blockTime ?? null,
        t2_observedAt: opp.t2_observedAt ?? null,
        t3_blockTime: opp.t3_blockTime ?? null,
        t3_observedAt: opp.t3_observedAt ?? null,
        halfClosureTimeSeconds: opp.halfClosureTimeSeconds ?? null,
        totalClosureTimeSeconds: opp.totalClosureTimeSeconds ?? null,
        initialGapBps: opp.initialGapBps ?? 0,
        postTradeGapBps: opp.postTradeGapBps ?? null,
        status: opp.status || 'detected',
        isBuyToken0: opp.isBuyToken0 ? 1 : 0,
        amountIn: opp.amountIn || '0',
        expectedOut: opp.expectedOut || null,
        actualOut: opp.actualOut || null,
        pnlToken0: opp.pnlToken0 || null,
        pnlToken1: opp.pnlToken1 || null,
        failureReason: opp.failureReason || null,
        isComplete: opp.isComplete ? 1 : 0,
        createdAt: opp.createdAt || Date.now(),
      });
    } else {
      const merged = { ...existing, ...opp };
      this.db.prepare(`
        UPDATE opportunities SET
          originChainId = @originChainId,
          destChainId = @destChainId,
          originTxHash = @originTxHash,
          lasnaTxHash = @lasnaTxHash,
          destTxHash = @destTxHash,
          t0_blockTime = @t0_blockTime,
          t0_observedAt = @t0_observedAt,
          t1_blockTime = @t1_blockTime,
          t1_observedAt = @t1_observedAt,
          t2_blockTime = @t2_blockTime,
          t2_observedAt = @t2_observedAt,
          t3_blockTime = @t3_blockTime,
          t3_observedAt = @t3_observedAt,
          halfClosureTimeSeconds = @halfClosureTimeSeconds,
          totalClosureTimeSeconds = @totalClosureTimeSeconds,
          initialGapBps = @initialGapBps,
          postTradeGapBps = @postTradeGapBps,
          status = @status,
          isBuyToken0 = @isBuyToken0,
          amountIn = @amountIn,
          expectedOut = @expectedOut,
          actualOut = @actualOut,
          pnlToken0 = @pnlToken0,
          pnlToken1 = @pnlToken1,
          failureReason = @failureReason,
          isComplete = @isComplete
        WHERE id = @id
      `).run({
        id: merged.id,
        originChainId: merged.originChainId,
        destChainId: merged.destChainId,
        originTxHash: merged.originTxHash?.toLowerCase() || null,
        lasnaTxHash: merged.lasnaTxHash?.toLowerCase() || null,
        destTxHash: merged.destTxHash?.toLowerCase() || null,
        t0_blockTime: merged.t0_blockTime ?? null,
        t0_observedAt: merged.t0_observedAt ?? null,
        t1_blockTime: merged.t1_blockTime ?? null,
        t1_observedAt: merged.t1_observedAt ?? null,
        t2_blockTime: merged.t2_blockTime ?? null,
        t2_observedAt: merged.t2_observedAt ?? null,
        t3_blockTime: merged.t3_blockTime ?? null,
        t3_observedAt: merged.t3_observedAt ?? null,
        halfClosureTimeSeconds: merged.halfClosureTimeSeconds ?? null,
        totalClosureTimeSeconds: merged.totalClosureTimeSeconds ?? null,
        initialGapBps: merged.initialGapBps,
        postTradeGapBps: merged.postTradeGapBps ?? null,
        status: merged.status,
        isBuyToken0: merged.isBuyToken0 ? 1 : 0,
        amountIn: merged.amountIn,
        expectedOut: merged.expectedOut || null,
        actualOut: merged.actualOut || null,
        pnlToken0: merged.pnlToken0 || null,
        pnlToken1: merged.pnlToken1 || null,
        failureReason: merged.failureReason || null,
        isComplete: merged.isComplete ? 1 : 0,
      });
    }
  }

  public getOpportunity(id: string): OpportunityRecord | null {
    const row = this.db.prepare('SELECT * FROM opportunities WHERE id = ?').get(id) as any;
    if (!row) return null;
    return {
      ...row,
      isBuyToken0: Boolean(row.isBuyToken0),
      isComplete: Boolean(row.isComplete),
    };
  }

  public getOpportunities(options?: { status?: string; limit?: number; offset?: number }): OpportunityRecord[] {
    let query = 'SELECT * FROM opportunities';
    const params: any[] = [];
    if (options?.status) {
      query += ' WHERE status = ?';
      params.push(options.status);
    }
    query += ' ORDER BY createdAt DESC';
    if (options?.limit) {
      query += ' LIMIT ?';
      params.push(options.limit);
      if (options?.offset) {
        query += ' OFFSET ?';
        params.push(options.offset);
      }
    }
    const rows = this.db.prepare(query).all(...params) as any[];
    return rows.map(r => ({
      ...r,
      isBuyToken0: Boolean(r.isBuyToken0),
      isComplete: Boolean(r.isComplete),
    }));
  }

  // Vault & System Health
  public upsertVaultState(v: VaultState) {
    this.db.prepare(`
      INSERT INTO vault_state (
        chainId, executorAddress, totalShares, reserve0, reserve1,
        isPaused, consecutiveFailures, lastUpdatedBlock
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(chainId) DO UPDATE SET
        totalShares = excluded.totalShares,
        reserve0 = excluded.reserve0,
        reserve1 = excluded.reserve1,
        isPaused = excluded.isPaused,
        consecutiveFailures = excluded.consecutiveFailures,
        lastUpdatedBlock = excluded.lastUpdatedBlock
    `).run(
      v.chainId, v.executorAddress.toLowerCase(), v.totalShares, v.reserve0, v.reserve1,
      v.isPaused ? 1 : 0, v.consecutiveFailures, v.lastUpdatedBlock
    );
  }

  public getVaultStates(): VaultState[] {
    const rows = this.db.prepare('SELECT * FROM vault_state').all() as any[];
    return rows.map(r => ({ ...r, isPaused: Boolean(r.isPaused) }));
  }

  public upsertUserShares(wallet: string, chainId: number, shares: string) {
    this.db.prepare(`
      INSERT INTO user_shares (walletAddress, chainId, shares, updatedAt)
      VALUES (?, ?, ?, ?)
      ON CONFLICT(walletAddress, chainId) DO UPDATE SET
        shares = excluded.shares,
        updatedAt = excluded.updatedAt
    `).run(wallet.toLowerCase(), chainId, shares, Date.now());
  }

  public getUserShares(wallet: string): { chainId: number; shares: string }[] {
    return this.db.prepare('SELECT chainId, shares FROM user_shares WHERE walletAddress = ?').all(wallet.toLowerCase()) as any[];
  }

  public setSystemHealth(key: string, value: string) {
    this.db.prepare(`
      INSERT INTO system_health (key, value, updatedAt)
      VALUES (?, ?, ?)
      ON CONFLICT(key) DO UPDATE SET
        value = excluded.value,
        updatedAt = excluded.updatedAt
    `).run(key, value, Date.now());
  }

  public getSystemHealth(): Record<string, string> {
    const rows = this.db.prepare('SELECT key, value FROM system_health').all() as { key: string; value: string }[];
    const result: Record<string, string> = {};
    for (const r of rows) result[r.key] = r.value;
    return result;
  }
}
