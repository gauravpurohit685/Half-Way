import { DB } from '../services/indexer/dist/db.js';
import { calculateLatencyStats, simulateCompetitiveBudget } from '../services/indexer/dist/stats.js';

const db = new DB('data/halfway.db');
const stats = calculateLatencyStats(db);
console.log('=== LATENCY LAB STATS ===');
console.log(JSON.stringify(stats, null, 2));

console.log('\n=== SIMULATED LATENCY BUDGET (h = 5.0s) ===');
const sim5 = simulateCompetitiveBudget(stats.endToEnd_T0_to_T3.p50_seconds, 5.0);
console.log(JSON.stringify(sim5, null, 2));

console.log('\n=== SIMULATED LATENCY BUDGET (h = 7.0s) ===');
const sim7 = simulateCompetitiveBudget(stats.endToEnd_T0_to_T3.p50_seconds, 7.0);
console.log(JSON.stringify(sim7, null, 2));
