import { DB } from './db.js';
import { LatencyStats, LatencyBudgetSimulation, OpportunityRecord } from './types.js';

function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index - lower;
  return Number((sorted[lower] * (1 - weight) + sorted[upper] * weight).toFixed(2));
}

export function calculateLatencyStats(db: DB): LatencyStats {
  const allOpps = db.getOpportunities({ limit: 10000 });
  const completeOpps = allOpps.filter(o => o.isComplete && o.t0_blockTime !== null && o.t1_blockTime !== null && o.t2_blockTime !== null && o.t3_blockTime !== null);

  const exclusions = {
    deadlineExpired: 0,
    slippageExceeded: 0,
    belowHurdle: 0,
    relayerPending: 0,
    other: 0,
  };

  for (const opp of allOpps) {
    if (!opp.isComplete) {
      if (opp.failureReason?.includes('DEADLINE')) exclusions.deadlineExpired++;
      else if (opp.failureReason?.includes('SLIPPAGE')) exclusions.slippageExceeded++;
      else if (opp.failureReason?.includes('HURDLE')) exclusions.belowHurdle++;
      else if (opp.status === 'detected' && !opp.destTxHash) exclusions.relayerPending++;
      else exclusions.other++;
    }
  }

  // Calculate hop delays for complete loops
  const hop1_sec: number[] = [];
  const hop1_ms: number[] = [];
  const hop2_sec: number[] = [];
  const hop2_ms: number[] = [];
  const hop3_sec: number[] = [];
  const hop3_ms: number[] = [];
  const total_sec: number[] = [];
  const total_ms: number[] = [];
  const t_half: number[] = [];
  const t_close: number[] = [];

  for (const o of completeOpps) {
    const h1_s = Math.max(0, o.t1_blockTime! - o.t0_blockTime!);
    const h2_s = Math.max(0, o.t2_blockTime! - o.t1_blockTime!);
    const h3_s = Math.max(0, o.t3_blockTime! - o.t2_blockTime!);
    const tot_s = Math.max(0, o.t3_blockTime! - o.t0_blockTime!);

    hop1_sec.push(h1_s);
    hop2_sec.push(h2_s);
    hop3_sec.push(h3_s);
    total_sec.push(tot_s);

    if (o.t0_observedAt && o.t1_observedAt) {
      hop1_ms.push(Math.max(0, o.t1_observedAt - o.t0_observedAt));
    }
    if (o.t1_observedAt && o.t2_observedAt) {
      hop2_ms.push(Math.max(0, o.t2_observedAt - o.t1_observedAt));
    }
    if (o.t2_observedAt && o.t3_observedAt) {
      hop3_ms.push(Math.max(0, o.t3_observedAt - o.t2_observedAt));
    }
    if (o.t0_observedAt && o.t3_observedAt) {
      total_ms.push(Math.max(0, o.t3_observedAt - o.t0_observedAt));
    }

    if (o.halfClosureTimeSeconds !== null) t_half.push(o.halfClosureTimeSeconds);
    if (o.totalClosureTimeSeconds !== null) t_close.push(o.totalClosureTimeSeconds);
  }

  const timestamps = allOpps.map(o => o.createdAt).filter(t => t > 0);
  const minTime = timestamps.length ? Math.min(...timestamps) : Date.now();
  const maxTime = timestamps.length ? Math.max(...timestamps) : Date.now();

  return {
    sampleSizeTotal: allOpps.length,
    sampleSizeComplete: completeOpps.length,
    dateRange: {
      start: new Date(minTime).toISOString(),
      end: new Date(maxTime).toISOString(),
    },
    exclusions,
    hop1_T0_to_T1: {
      p50_seconds: percentile(hop1_sec, 50),
      p90_seconds: percentile(hop1_sec, 90),
      max_seconds: hop1_sec.length ? Math.max(...hop1_sec) : 0,
      p50_observed_ms: percentile(hop1_ms, 50),
      p90_observed_ms: percentile(hop1_ms, 90),
      max_observed_ms: hop1_ms.length ? Math.max(...hop1_ms) : 0,
    },
    hop2_T1_to_T2: {
      p50_seconds: percentile(hop2_sec, 50),
      p90_seconds: percentile(hop2_sec, 90),
      max_seconds: hop2_sec.length ? Math.max(...hop2_sec) : 0,
      p50_observed_ms: percentile(hop2_ms, 50),
      p90_observed_ms: percentile(hop2_ms, 90),
      max_observed_ms: hop2_ms.length ? Math.max(...hop2_ms) : 0,
    },
    hop3_T2_to_T3: {
      p50_seconds: percentile(hop3_sec, 50),
      p90_seconds: percentile(hop3_sec, 90),
      max_seconds: hop3_sec.length ? Math.max(...hop3_sec) : 0,
      p50_observed_ms: percentile(hop3_ms, 50),
      p90_observed_ms: percentile(hop3_ms, 90),
      max_observed_ms: hop3_ms.length ? Math.max(...hop3_ms) : 0,
    },
    endToEnd_T0_to_T3: {
      p50_seconds: percentile(total_sec, 50),
      p90_seconds: percentile(total_sec, 90),
      max_seconds: total_sec.length ? Math.max(...total_sec) : 0,
      p50_observed_ms: percentile(total_ms, 50),
      p90_observed_ms: percentile(total_ms, 90),
      max_observed_ms: total_ms.length ? Math.max(...total_ms) : 0,
    },
    halfClosure_T_half: {
      p50_seconds: percentile(t_half, 50),
      p90_seconds: percentile(t_half, 90),
    },
    totalClosure_T_close: {
      p50_seconds: percentile(t_close, 50),
      p90_seconds: percentile(t_close, 90),
    },
  };
}

export function simulateCompetitiveBudget(
  testedLatencySeconds: number,
  assumedCompetitorHalfLifeSeconds: number = 5.0
): LatencyBudgetSimulation {
  const h = Math.max(0.1, assumedCompetitorHalfLifeSeconds);
  const L = Math.max(0, testedLatencySeconds);
  // Share = (1/2)^(L / h)
  const fraction = Math.pow(0.5, L / h);
  const retainedPercent = Number((fraction * 100).toFixed(2));
  const lossPercent = Number((100 - retainedPercent).toFixed(2));

  return {
    modelType: 'EXPONENTIAL_DECAY_SIMULATION',
    assumedCompetitorHalfLifeSeconds: h,
    testedLatencySeconds: L,
    retainedOpportunitySharePercent: retainedPercent,
    theoreticalLossPercent: lossPercent,
    description: `[SIMULATION MODEL] At h = ${h.toFixed(1)}s (assumed competitor half-life), our loop of ${L.toFixed(1)}s captures ${retainedPercent.toFixed(1)}% of the theoretical maximum opportunity.`,
  };
}
