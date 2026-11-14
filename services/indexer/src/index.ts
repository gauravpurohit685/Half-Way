import { DB } from './db.js';
import { config } from './config.js';
import { IndexerService } from './indexer.js';
import { createServer } from './server.js';

async function main() {
  console.log('====================================================');
  console.log('   Halfway — Reactive Omni Indexer & Latency Lab    ');
  console.log('====================================================');

  const db = new DB(config.dbPath);
  console.log(`[DB] SQLite database initialized at ${config.dbPath}`);

  const indexer = new IndexerService(db);
  await indexer.start();

  const server = createServer(db);
  const host = '0.0.0.0';
  const port = config.port;

  await server.listen({ host, port });
  console.log(`[API] Server listening on http://localhost:${port}`);
  console.log(`[API] SSE stream active at http://localhost:${port}/api/events`);

  const shutdown = async () => {
    console.log('[System] Shutting down indexer and API server...');
    indexer.stop();
    await server.close();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch(err => {
  console.error('[Fatal Error]:', err);
  process.exit(1);
});
