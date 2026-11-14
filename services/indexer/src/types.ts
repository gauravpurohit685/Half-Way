export type HopStatus = 'pending' | 'detected' | 'executed' | 'closed' | 'skipped' | 'failed';

export interface OpportunityRecord {
  id: string; // bytes32 hex
  originChainId: number;
  destChainId: number;
  originTxHash: string | null;
  lasnaTxHash: string | null;
  destTxHash: string | null;
  t0_blockTime: number | null; // seconds
  t0_observedAt: number | null; // ms (calibrated)
  t1_blockTime: number | null; // seconds
  t1_observedAt: number | null; // ms
  t2_blockTime: number | null; // seconds
  t2_observedAt: number | null; // ms
  t3_blockTime: number | null; // seconds
  t3_observedAt: number | null; // ms
  halfClosureTimeSeconds: number | null; // T1/2
  totalClosureTimeSeconds: number | null; // T_close
  initialGapBps: number;
  postTradeGapBps: number | null;
  status: HopStatus;
  isBuyToken0: boolean;
  amountIn: string;
  expectedOut: string | null;
  actualOut: string | null;
  pnlToken0: string | null;
  pnlToken1: string | null;
  failureReason: string | null;
  isComplete: boolean;
  createdAt: number;
}

export interface PoolState {
  chainId: number;
  address: string;
  token0: string;
  token1: string;
  reserve0: string;
  reserve1: string;
  normalizedPrice: string; // scaled to 1e18
  lastBlockNumber: number;
  lastBlockTimestamp: number;
  lastObservedAt: number;
}

export interface VaultState {
  chainId: number;
  executorAddress: string;
  totalShares: string;
  reserve0: string;
  reserve1: string;
  isPaused: boolean;
  consecutiveFailures: number;
  lastUpdatedBlock: number;
}

export interface LatencyStats {
  sampleSizeTotal: number;
  sampleSizeComplete: number;
  dateRange: {
    start: string;
    end: string;
  };
  exclusions: {
    deadlineExpired: number;
    slippageExceeded: number;
    belowHurdle: number;
    relayerPending: number;
    other: number;
  };
  hop1_T0_to_T1: {
    p50_seconds: number;
    p90_seconds: number;
    max_seconds: number;
    p50_observed_ms: number;
    p90_observed_ms: number;
    max_observed_ms: number;
  };
  hop2_T1_to_T2: {
    p50_seconds: number;
    p90_seconds: number;
    max_seconds: number;
    p50_observed_ms: number;
    p90_observed_ms: number;
    max_observed_ms: number;
  };
  hop3_T2_to_T3: {
    p50_seconds: number;
    p90_seconds: number;
    max_seconds: number;
    p50_observed_ms: number;
    p90_observed_ms: number;
    max_observed_ms: number;
  };
  endToEnd_T0_to_T3: {
    p50_seconds: number;
    p90_seconds: number;
    max_seconds: number;
    p50_observed_ms: number;
    p90_observed_ms: number;
    max_observed_ms: number;
  };
  halfClosure_T_half: {
    p50_seconds: number;
    p90_seconds: number;
  };
  totalClosure_T_close: {
    p50_seconds: number;
    p90_seconds: number;
  };
}

export interface LatencyBudgetSimulation {
  modelType: 'EXPONENTIAL_DECAY_SIMULATION';
  assumedCompetitorHalfLifeSeconds: number;
  testedLatencySeconds: number;
  retainedOpportunitySharePercent: number;
  theoreticalLossPercent: number;
  description: string;
}
