import { createPublicClient, http, parseAbiItem, decodeEventLog, formatEther } from 'viem';
import { EventEmitter } from 'events';
import { config } from './config.js';
import { DB } from './db.js';
import { ClockSync } from './clock_sync.js';
import { PoolState, VaultState } from './types.js';

export const liveEvents = new EventEmitter();

// ABI Items for decoding
const SYNC_EVENT = parseAbiItem('event Sync(uint112 reserve0, uint112 reserve1)');
const SWAP_EVENT = parseAbiItem('event Swap(address indexed sender, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out, address indexed to)');
const OPP_DETECTED_EVENT = parseAbiItem('event OpportunityDetected(bytes32 indexed opportunityId, uint256 originChainId, uint256 destChainId, uint256 originPrice, uint256 destPrice, uint256 spreadBps, bool isBuyToken0, uint256 amountIn, uint256 timestamp)');
const CALLBACK_DISPATCHED_EVENT = parseAbiItem('event CallbackDispatched(bytes32 indexed opportunityId, uint256 destChainId, address destExecutor, uint256 amountIn, uint256 minAmountOut, uint256 deadline)');
const LEG_EXECUTED_EVENT = parseAbiItem('event LegExecuted(bytes32 indexed opportunityId, bool isBuyToken0, uint256 amountIn, uint256 amountOut, uint256 timestamp)');
const LEG_SKIPPED_EVENT = parseAbiItem('event LegSkipped(bytes32 indexed opportunityId, string reason, uint256 timestamp)');
const LEG_FAILED_EVENT = parseAbiItem('event LegFailed(bytes32 indexed opportunityId, string reason, uint256 timestamp)');
const DEPOSITED_EVENT = parseAbiItem('event Deposited(address indexed user, uint256 amount0, uint256 amount1, uint256 shares, uint256 timestamp)');
const WITHDRAWN_EVENT = parseAbiItem('event Withdrawn(address indexed user, uint256 shares, uint256 amount0, uint256 amount1, uint256 timestamp)');

export class IndexerService {
  private db: DB;
  private running: boolean = false;
  private clients: {
    baseSepolia: ReturnType<typeof createPublicClient>;
    unichainSepolia: ReturnType<typeof createPublicClient>;
    reactiveLasna: ReturnType<typeof createPublicClient>;
  };

  constructor(db: DB) {
    this.db = db;

    this.clients = {
      baseSepolia: createPublicClient({
        transport: http(config.chains.baseSepolia.rpcUrl, { retryCount: 3, timeout: 10_000 }),
      }),
      unichainSepolia: createPublicClient({
        transport: http(config.chains.unichainSepolia.rpcUrl, { retryCount: 3, timeout: 10_000 }),
      }),
      reactiveLasna: createPublicClient({
        transport: http(config.chains.reactiveLasna.rpcUrl, { retryCount: 3, timeout: 10_000 }),
      }),
    };
  }

  public async start() {
    this.running = true;
    console.log('[Indexer] Initializing on-chain event pollers...');

    // Calibrate clock offset
    const offset = await ClockSync.measure();
    console.log(`[Indexer] Calibrated WSL Clock Offset: ${offset}ms`);
    this.db.setSystemHealth('clock_offset_ms', offset.toString());

    // Backfill & start polling loops
    this.pollChain('baseSepolia', config.chains.baseSepolia);
    this.pollChain('unichainSepolia', config.chains.unichainSepolia);
    this.pollChain('reactiveLasna', config.chains.reactiveLasna);
    this.pollSystemHealth();
  }

  public stop() {
    this.running = false;
  }

  private sanitizeError(msg: string): string {
    return msg.replace(/https?:\/\/[^\s"'`]+/g, '[REDACTED_RPC]');
  }

  private async pollChain(chainKey: 'baseSepolia' | 'unichainSepolia' | 'reactiveLasna', chainConf: any) {
    const client = this.clients[chainKey];
    const chainId = chainConf.id;
    const chunkSize = chainConf.chunkSize || 100;

    let fromBlock: number = this.db.getCheckpoint(chainId) ?? chainConf.startBlock;
    if (fromBlock < chainConf.startBlock) {
      fromBlock = chainConf.startBlock;
    }

    console.log(`[Indexer] ${chainConf.name} indexing starting from block ${fromBlock}`);

    while (this.running) {
      try {
        const latestBlockBigInt = await client.getBlockNumber();
        const latestBlock = Number(latestBlockBigInt);

        if (latestBlock >= fromBlock) {
          const toBlock = Math.min(fromBlock + chunkSize, latestBlock);

          await this.processBlockRange(chainKey, chainConf, BigInt(fromBlock), BigInt(toBlock));

          this.db.setCheckpoint(chainId, toBlock + 1);
          fromBlock = toBlock + 1;

          // If still backfilling catching up to head, continue immediately
          if (fromBlock < latestBlock) {
            continue;
          }
        }

        // Sleep poll interval once caught up
        await new Promise(r => setTimeout(r, chainConf.pollIntervalMs));
      } catch (err: any) {
        console.error(`[Indexer] Error polling ${chainConf.name}:`, this.sanitizeError(err.shortMessage || err.message || String(err)));
        await new Promise(r => setTimeout(r, 4000)); // Backoff on error
      }
    }
  }

  private async processBlockRange(
    chainKey: 'baseSepolia' | 'unichainSepolia' | 'reactiveLasna',
    chainConf: any,
    fromBlock: bigint,
    toBlock: bigint
  ) {
    const client = this.clients[chainKey];
    const chainId = chainConf.id;

    // Determine addresses to watch for this chain
    const addresses: `0x${string}`[] = [];
    if (chainConf.contracts.HalfPair) addresses.push(chainConf.contracts.HalfPair);
    if (chainConf.contracts.HalfwayExecutor) addresses.push(chainConf.contracts.HalfwayExecutor);
    if (chainConf.contracts.HalfwayReactive) addresses.push(chainConf.contracts.HalfwayReactive);

    if (addresses.length === 0) return;

    for (const address of addresses) {
      const logs = await client.getLogs({
        address,
        fromBlock,
        toBlock,
      });

      for (const log of logs) {
        await this.handleLog(chainKey, chainConf, log);
      }
    }
  }

  private async handleLog(
    chainKey: 'baseSepolia' | 'unichainSepolia' | 'reactiveLasna',
    chainConf: any,
    log: any
  ) {
    const client = this.clients[chainKey];
    const chainId = chainConf.id;
    const observedAt = ClockSync.now();

    // Fetch block timestamp
    let blockTime = Math.floor(Date.now() / 1000);
    try {
      const block = await client.getBlock({ blockNumber: log.blockNumber });
      blockTime = Number(block.timestamp);
    } catch {}

    const rawTxHash = log.transactionHash;
    const logIndex = Number(log.logIndex);

    // 1. Sync Event (Pool Reserves Update)
    try {
      const decoded = decodeEventLog({ abi: [SYNC_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'Sync') {
        const { reserve0, reserve1 } = decoded.args as any;
        const r0Big = BigInt(reserve0.toString());
        const r1Big = BigInt(reserve1.toString());
        // Price = (reserve1 * 1e18) / reserve0
        const price = r0Big > 0n ? ((r1Big * 10n ** 18n) / r0Big).toString() : '0';

        const poolState: PoolState = {
          chainId,
          address: log.address.toLowerCase(),
          token0: chainConf.contracts.MockERC20 || '',
          token1: chainConf.contracts.MockERC20 || '',
          reserve0: reserve0.toString(),
          reserve1: reserve1.toString(),
          normalizedPrice: price,
          lastBlockNumber: Number(log.blockNumber),
          lastBlockTimestamp: blockTime,
          lastObservedAt: observedAt,
        };
        this.db.upsertPool(poolState);

        this.db.insertEvent({
          chainId,
          blockNumber: Number(log.blockNumber),
          txHash: rawTxHash,
          logIndex,
          eventName: 'Sync',
          contractAddress: log.address,
          dataJson: JSON.stringify({ reserve0: reserve0.toString(), reserve1: reserve1.toString(), price }),
          blockTime,
          observedAt,
        });

        liveEvents.emit('pool_sync', poolState);
        this.checkGapAndConvergence(poolState, blockTime, observedAt);
      }
    } catch {}

    // 2. Swap Event (Origin or Leg Swap)
    try {
      const decoded = decodeEventLog({ abi: [SWAP_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'Swap') {
        const { sender, amount0In, amount1In, amount0Out, amount1Out, to } = decoded.args as any;
        this.db.insertEvent({
          chainId,
          blockNumber: Number(log.blockNumber),
          txHash: rawTxHash,
          logIndex,
          eventName: 'Swap',
          contractAddress: log.address,
          dataJson: JSON.stringify({
            sender,
            amount0In: amount0In.toString(),
            amount1In: amount1In.toString(),
            amount0Out: amount0Out.toString(),
            amount1Out: amount1Out.toString(),
            to,
          }),
          blockTime,
          observedAt,
        });
        liveEvents.emit('swap', { chainId, txHash: rawTxHash, blockTime, observedAt });
      }
    } catch {}

    // 3. OpportunityDetected Event (Reactive Lasna)
    try {
      const decoded = decodeEventLog({ abi: [OPP_DETECTED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'OpportunityDetected') {
        const { opportunityId, originChainId, destChainId, spreadBps, isBuyToken0, amountIn } = decoded.args as any;
        const idHex = opportunityId.toLowerCase();

        this.db.upsertOpportunity({
          id: idHex,
          originChainId: Number(originChainId),
          destChainId: Number(destChainId),
          lasnaTxHash: rawTxHash,
          t1_blockTime: blockTime,
          t1_observedAt: observedAt,
          initialGapBps: Number(spreadBps),
          status: 'detected',
          isBuyToken0: Boolean(isBuyToken0),
          amountIn: amountIn.toString(),
          createdAt: observedAt,
          isComplete: false,
        });

        // Correlate T0 by finding latest origin swap
        this.correlateT0(idHex, Number(originChainId), blockTime, observedAt);

        this.db.insertEvent({
          chainId,
          blockNumber: Number(log.blockNumber),
          txHash: rawTxHash,
          logIndex,
          eventName: 'OpportunityDetected',
          contractAddress: log.address,
          dataJson: JSON.stringify({ opportunityId: idHex, spreadBps: Number(spreadBps), amountIn: amountIn.toString() }),
          blockTime,
          observedAt,
        });

        liveEvents.emit('opportunity_detected', { id: idHex, spreadBps: Number(spreadBps) });
      }
    } catch {}

    // 4. CallbackDispatched Event (Reactive Lasna)
    try {
      const decoded = decodeEventLog({ abi: [CALLBACK_DISPATCHED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'CallbackDispatched') {
        const { opportunityId, destExecutor, amountIn, minAmountOut, deadline } = decoded.args as any;
        const idHex = opportunityId.toLowerCase();
        this.db.upsertOpportunity({
          id: idHex,
          expectedOut: minAmountOut.toString(),
        });
      }
    } catch {}

    // 5. LegExecuted Event (Destination Executor)
    try {
      const decoded = decodeEventLog({ abi: [LEG_EXECUTED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'LegExecuted') {
        const { opportunityId, isBuyToken0, amountIn, amountOut } = decoded.args as any;
        const idHex = opportunityId.toLowerCase();

        this.db.upsertOpportunity({
          id: idHex,
          destTxHash: rawTxHash,
          t2_blockTime: blockTime,
          t2_observedAt: observedAt,
          actualOut: amountOut.toString(),
          status: 'executed',
        });

        this.db.insertEvent({
          chainId,
          blockNumber: Number(log.blockNumber),
          txHash: rawTxHash,
          logIndex,
          eventName: 'LegExecuted',
          contractAddress: log.address,
          dataJson: JSON.stringify({ opportunityId: idHex, amountIn: amountIn.toString(), amountOut: amountOut.toString() }),
          blockTime,
          observedAt,
        });

        liveEvents.emit('leg_executed', { id: idHex, txHash: rawTxHash });
      }
    } catch {}

    // 6. LegSkipped / LegFailed Event
    try {
      const decoded = decodeEventLog({ abi: [LEG_SKIPPED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'LegSkipped') {
        const { opportunityId, reason } = decoded.args as any;
        const idHex = opportunityId.toLowerCase();
        this.db.upsertOpportunity({
          id: idHex,
          destTxHash: rawTxHash,
          status: 'skipped',
          failureReason: reason,
          t2_blockTime: blockTime,
          t2_observedAt: observedAt,
        });
      }
    } catch {}

    try {
      const decoded = decodeEventLog({ abi: [LEG_FAILED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'LegFailed') {
        const { opportunityId, reason } = decoded.args as any;
        const idHex = opportunityId.toLowerCase();
        this.db.upsertOpportunity({
          id: idHex,
          destTxHash: rawTxHash,
          status: 'failed',
          failureReason: reason,
          t2_blockTime: blockTime,
          t2_observedAt: observedAt,
        });
      }
    } catch {}

    // 7. Deposited / Withdrawn Events
    try {
      const decoded = decodeEventLog({ abi: [DEPOSITED_EVENT], data: log.data, topics: log.topics });
      if (decoded.eventName === 'Deposited') {
        const { user, shares } = decoded.args as any;
        this.db.upsertUserShares(user, chainId, shares.toString());
      }
    } catch {}
  }

  private correlateT0(idHex: string, originChainId: number, t1_blockTime: number, t1_observedAt: number) {
    // Look up the most recent swap event on origin chain that preceded T1
    const swapEvent = this.db.db.prepare(`
      SELECT txHash, blockTime, observedAt FROM events
      WHERE chainId = ? AND eventName = 'Swap' AND blockTime <= ?
      ORDER BY blockTime DESC, id DESC LIMIT 1
    `).get(originChainId, t1_blockTime) as any;

    if (swapEvent) {
      this.db.upsertOpportunity({
        id: idHex,
        originTxHash: swapEvent.txHash,
        t0_blockTime: swapEvent.blockTime,
        t0_observedAt: swapEvent.observedAt,
      });
    } else {
      // Default T0 block to T1 - 2s if event log was just before start block
      this.db.upsertOpportunity({
        id: idHex,
        t0_blockTime: t1_blockTime - 2,
        t0_observedAt: t1_observedAt - 2000,
      });
    }
  }

  private checkGapAndConvergence(latestPool: PoolState, blockTime: number, observedAt: number) {
    // Check gap against peer pool
    const peerChainId = latestPool.chainId === 84532 ? 1301 : 84532;
    const peerConf = peerChainId === 84532 ? config.chains.baseSepolia : config.chains.unichainSepolia;
    const peerPool = this.db.getPool(peerChainId, peerConf.contracts.HalfPair);

    if (!peerPool) return;

    const priceA = BigInt(latestPool.normalizedPrice);
    const priceB = BigInt(peerPool.normalizedPrice);
    if (priceA === 0n || priceB === 0n) return;

    const diff = priceA > priceB ? priceA - priceB : priceB - priceA;
    const ref = priceA > priceB ? priceB : priceA;
    const gapBps = Number((diff * 10000n) / ref);

    // If an open opportunity is pending convergence
    const pendingOpps = this.db.db.prepare(`
      SELECT * FROM opportunities
      WHERE status IN ('detected', 'executed') AND isComplete = 0
      ORDER BY createdAt DESC LIMIT 5
    `).all() as any[];

    for (const opp of pendingOpps) {
      // Check half-closure (50% reduction in spread)
      const halfThreshold = opp.initialGapBps / 2;
      if (gapBps <= halfThreshold && !opp.halfClosureTimeSeconds && opp.t0_blockTime) {
        const halfTimeSec = Math.max(0, blockTime - opp.t0_blockTime);
        this.db.upsertOpportunity({
          id: opp.id,
          halfClosureTimeSeconds: halfTimeSec,
        });
      }

      // Check full convergence (below strategy threshold 50 bps)
      if (gapBps <= 50 && opp.t0_blockTime) {
        const totalTimeSec = Math.max(0, blockTime - opp.t0_blockTime);
        this.db.upsertOpportunity({
          id: opp.id,
          t3_blockTime: blockTime,
          t3_observedAt: observedAt,
          totalClosureTimeSeconds: totalTimeSec,
          postTradeGapBps: gapBps,
          status: 'closed',
          isComplete: true,
        });
        liveEvents.emit('gap_closed', { id: opp.id, totalTimeSec, postTradeGapBps: gapBps });
      }
    }
  }

  private async pollSystemHealth() {
    while (this.running) {
      try {
        // Read Lasna reactive balance
        const lasnaClient = this.clients.reactiveLasna;
        const reactiveAddr = config.chains.reactiveLasna.contracts.HalfwayReactive;
        if (reactiveAddr) {
          const bal = await lasnaClient.getBalance({ address: reactiveAddr });
          this.db.setSystemHealth('lasna_lreact_balance', formatEther(bal));
        }

        // Vault status checks
        for (const [chainKey, chainConf] of [
          ['baseSepolia', config.chains.baseSepolia],
          ['unichainSepolia', config.chains.unichainSepolia],
        ] as const) {
          const client = this.clients[chainKey];
          const execAddr = chainConf.contracts.HalfwayExecutor;
          if (execAddr) {
            // Read pool reserves for vault snapshot
            const poolState = this.db.getPool(chainConf.id, chainConf.contracts.HalfPair);
            const vaultState: VaultState = {
              chainId: chainConf.id,
              executorAddress: execAddr.toLowerCase(),
              totalShares: '1000000000000000000', // non-zero default
              reserve0: poolState?.reserve0 || '0',
              reserve1: poolState?.reserve1 || '0',
              isPaused: false,
              consecutiveFailures: 0,
              lastUpdatedBlock: poolState?.lastBlockNumber || 0,
            };
            this.db.upsertVaultState(vaultState);
          }
        }
      } catch (err: any) {
        // Suppress transient health check errors
      }
      await new Promise(r => setTimeout(r, 10_000));
    }
  }
}
