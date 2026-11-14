import Fastify from 'fastify';
import cors from '@fastify/cors';
import { DB } from './db.js';
import { config } from './config.js';
import { calculateLatencyStats, simulateCompetitiveBudget } from './stats.js';
import { liveEvents } from './indexer.js';

export function createServer(db: DB) {
  const app = Fastify({ logger: false });

  app.register(cors, {
    origin: '*',
  });

  // 1. Config Endpoint
  app.get('/api/config', async () => {
    return {
      chains: config.chains,
      version: '1.0.0',
      network: 'testnet',
    };
  });

  // 2. Prices & Gap Endpoint
  app.get('/api/prices', async () => {
    const pools = db.getAllPools();
    const poolBase = pools.find(p => p.chainId === 84532);
    const poolUni = pools.find(p => p.chainId === 1301);

    let gapBps = 0;
    if (poolBase && poolUni) {
      const pA = BigInt(poolBase.normalizedPrice);
      const pB = BigInt(poolUni.normalizedPrice);
      if (pA > 0n && pB > 0n) {
        const diff = pA > pB ? pA - pB : pB - pA;
        const ref = pA > pB ? pB : pA;
        gapBps = Number((diff * 10000n) / ref);
      }
    }

    return {
      pools,
      normalizedGapBps: gapBps,
      thresholdBps: 50,
      timestamp: Date.now(),
    };
  });

  // 3. Opportunities Feed
  app.get('/api/opportunities', async (request) => {
    const query = request.query as { status?: string; limit?: string; offset?: string };
    const limit = query.limit ? parseInt(query.limit, 10) : 50;
    const offset = query.offset ? parseInt(query.offset, 10) : 0;

    const opportunities = db.getOpportunities({
      status: query.status,
      limit,
      offset,
    });

    return {
      count: opportunities.length,
      opportunities,
    };
  });

  // 4. Opportunity Detail
  app.get('/api/opportunities/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const opp = db.getOpportunity(id.toLowerCase());
    if (!opp) {
      return reply.code(404).send({ error: 'Opportunity not found' });
    }

    const originExplorer = opp.originChainId === 84532 ? config.chains.baseSepolia.explorerUrl : config.chains.unichainSepolia.explorerUrl;
    const destExplorer = opp.destChainId === 84532 ? config.chains.baseSepolia.explorerUrl : config.chains.unichainSepolia.explorerUrl;
    const lasnaExplorer = config.chains.reactiveLasna.explorerUrl;

    return {
      ...opp,
      explorers: {
        originTxUrl: opp.originTxHash ? `${originExplorer}/tx/${opp.originTxHash}` : null,
        lasnaTxUrl: opp.lasnaTxHash ? `${lasnaExplorer}/tx/${opp.lasnaTxHash}` : null,
        destTxUrl: opp.destTxHash ? `${destExplorer}/tx/${opp.destTxHash}` : null,
      },
      hops: [
        {
          name: 'T0: Origin Swap Inclusion',
          blockTime: opp.t0_blockTime,
          observedAt: opp.t0_observedAt,
          txHash: opp.originTxHash,
          source: 'block_header + observer',
        },
        {
          name: 'T1: Reactive Lasna Processing',
          blockTime: opp.t1_blockTime,
          observedAt: opp.t1_observedAt,
          txHash: opp.lasnaTxHash,
          source: 'block_header + observer',
        },
        {
          name: 'T2: Destination Callback Execution',
          blockTime: opp.t2_blockTime,
          observedAt: opp.t2_observedAt,
          txHash: opp.destTxHash,
          source: 'block_header + observer',
        },
        {
          name: 'T3: Gap Convergence',
          blockTime: opp.t3_blockTime,
          observedAt: opp.t3_observedAt,
          source: 'pool_reserves_sync',
        },
      ],
    };
  });

  // 5. Aggregate Latency Stats (Measured Only)
  app.get('/api/stats', async () => {
    return calculateLatencyStats(db);
  });

  // 6. Latency Budget Simulation (SIMULATED Model)
  app.get('/api/simulation', async (request) => {
    const query = request.query as { h?: string; l?: string };
    const h = query.h ? parseFloat(query.h) : 5.0;
    const l = query.l ? parseFloat(query.l) : 2.0;

    return simulateCompetitiveBudget(l, h);
  });

  // 7. Vault & System Health
  app.get('/api/vault', async (request) => {
    const query = request.query as { wallet?: string };
    const vaults = db.getVaultStates();
    const systemHealth = db.getSystemHealth();

    let userShares = null;
    if (query.wallet) {
      userShares = db.getUserShares(query.wallet);
    }

    return {
      vaults,
      systemHealth,
      userShares,
    };
  });

  // 8. Server-Sent Events (SSE) Live Feed
  app.get('/api/events', async (request, reply) => {
    reply.raw.setHeader('Content-Type', 'text/event-stream');
    reply.raw.setHeader('Cache-Control', 'no-cache');
    reply.raw.setHeader('Connection', 'keep-alive');
    reply.raw.setHeader('Access-Control-Allow-Origin', '*');
    reply.raw.flushHeaders();

    const onPoolSync = (data: any) => {
      reply.raw.write(`event: pool_sync\ndata: ${JSON.stringify(data)}\n\n`);
    };

    const onSwap = (data: any) => {
      reply.raw.write(`event: swap\ndata: ${JSON.stringify(data)}\n\n`);
    };

    const onOpp = (data: any) => {
      reply.raw.write(`event: opportunity_detected\ndata: ${JSON.stringify(data)}\n\n`);
    };

    const onLeg = (data: any) => {
      reply.raw.write(`event: leg_executed\ndata: ${JSON.stringify(data)}\n\n`);
    };

    const onGapClosed = (data: any) => {
      reply.raw.write(`event: gap_closed\ndata: ${JSON.stringify(data)}\n\n`);
    };

    liveEvents.on('pool_sync', onPoolSync);
    liveEvents.on('swap', onSwap);
    liveEvents.on('opportunity_detected', onOpp);
    liveEvents.on('leg_executed', onLeg);
    liveEvents.on('gap_closed', onGapClosed);

    request.raw.on('close', () => {
      liveEvents.off('pool_sync', onPoolSync);
      liveEvents.off('swap', onSwap);
      liveEvents.off('opportunity_detected', onOpp);
      liveEvents.off('leg_executed', onLeg);
      liveEvents.off('gap_closed', onGapClosed);
    });
  });

  return app;
}
