import https from 'https';

export class ClockSync {
  private static offsetMs: number = 0;
  private static lastMeasuredAt: number = 0;

  public static async measure(): Promise<number> {
    return new Promise((resolve) => {
      const start = Date.now();
      const req = https.get('https://cloudflare.com/cdn-cgi/trace', { timeout: 4000 }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          const end = Date.now();
          const rtt = end - start;
          const match = data.match(/ts=(\d+\.\d+)/);
          if (match) {
            const serverMs = Math.round(parseFloat(match[1]) * 1000);
            const localEstimated = start + (rtt / 2);
            ClockSync.offsetMs = serverMs - localEstimated;
            ClockSync.lastMeasuredAt = Date.now();
            resolve(ClockSync.offsetMs);
          } else {
            const serverDate = res.headers.date ? new Date(res.headers.date).getTime() : Date.now();
            ClockSync.offsetMs = serverDate - (start + rtt / 2);
            ClockSync.lastMeasuredAt = Date.now();
            resolve(ClockSync.offsetMs);
          }
        });
      });

      req.on('error', () => {
        // Fallback to Google HEAD
        const gStart = Date.now();
        const gReq = https.request('https://www.google.com', { method: 'HEAD', timeout: 3000 }, (gRes) => {
          const gEnd = Date.now();
          const gRtt = gEnd - gStart;
          const sDate = gRes.headers.date ? new Date(gRes.headers.date).getTime() : Date.now();
          ClockSync.offsetMs = sDate - (gStart + gRtt / 2);
          ClockSync.lastMeasuredAt = Date.now();
          resolve(ClockSync.offsetMs);
        });
        gReq.on('error', () => {
          resolve(ClockSync.offsetMs);
        });
        gReq.end();
      });
    });
  }

  public static getOffset(): number {
    return ClockSync.offsetMs;
  }

  public static now(): number {
    return Date.now() + ClockSync.offsetMs;
  }
}
