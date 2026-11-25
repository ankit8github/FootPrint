/** Loopback-only benchmark fixture: archived assets, no corpus serving or HMR. */
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { gzipSync } from 'node:zlib';
import { inventory } from './build.mjs';

export async function productionServer(directory, { port = 5185, apiPort = 8000 } = {}) {
  const assets = await inventory(directory);
  const graph = JSON.parse(await fs.readFile(directory + '-inventory.json', 'utf8'));
  const buffers = new Map();
  for (const asset of assets) buffers.set('/' + asset.file, await fs.readFile(path.join(directory, asset.file)));
  const html = buffers.get('/index.html');
  const nonce = html?.toString().match(/<meta property="csp-nonce" nonce="([A-Za-z0-9+/=]+)"/u)?.[1];
  if (!nonce) throw new Error('Expected production CSP nonce');
  const routes = new Set(['/', '/phase2', '/phase3', '/phase4', '/phase5']);
  const ledger = [];
  const server = http.createServer(async (request, response) => {
    const record = { path: request.url, method: request.method, bodyBytes: 0, encoding: 'identity', status: 0, completed: false };
    ledger.push(record);
    const send = (status, buffer, type) => {
      record.status = status;
      const compress = status === 200 && /\bgzip\b/u.test(request.headers['accept-encoding'] ?? '');
      const data = compress ? gzipSync(buffer, { level: 6 }) : buffer;
      record.bodyBytes = data.length; record.encoding = compress ? 'gzip' : 'identity';
      response.writeHead(status, { 'Content-Type': type, 'Content-Length': data.length,
        ...(compress ? { 'Content-Encoding': 'gzip' } : {}), Vary: 'Accept-Encoding',
        Connection: 'close',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
        'Content-Security-Policy': `default-src 'self'; script-src 'self' 'nonce-${nonce}'; style-src 'self' 'unsafe-inline'; connect-src 'self'; worker-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'` });
      response.once('finish', () => {
        record.completed = true;
        // One HTTP/1.1 request per connection gives public socket byte counters
        // exact request+response payload accounting, including worker scripts.
        record.socketReadBytes = request.socket.bytesRead;
        record.socketWrittenBytes = request.socket.bytesWritten;
      });
      response.end(data);
    };
    try {
      if (request.headers.host !== `127.0.0.1:${port}` || request.method !== 'GET' || request.headers.cookie || request.headers.authorization ||
          request.headers['transfer-encoding'] || Number(request.headers['content-length'] ?? 0) !== 0) {
        send(400, Buffer.from('{"code":"BENCHMARK_REJECTED"}'), 'application/json'); return;
      }
      if (request.url === '/api/v1/demo') {
        const upstream = await fetch(`http://127.0.0.1:${apiPort}/api/v1/demo`, { redirect: 'error', signal: AbortSignal.timeout(5000) });
        if (!upstream.ok) throw new Error('Demo backend unavailable');
        send(200, Buffer.from(await upstream.arrayBuffer()), 'application/json');
      } else if (routes.has(request.url)) send(200, html, 'text/html; charset=utf-8');
      else if (request.url === '/favicon.ico') send(204, Buffer.alloc(0), 'image/x-icon');
      else if (buffers.has(request.url) && request.url.startsWith('/assets/')) {
        send(200, buffers.get(request.url), request.url.endsWith('.js') ? 'text/javascript' : request.url.endsWith('.css') ? 'text/css' : 'application/octet-stream');
      } else send(404, Buffer.from('{"code":"BENCHMARK_REJECTED"}'), 'application/json');
    } catch { if (!response.headersSent) send(503, Buffer.from('{"code":"BENCHMARK_UNAVAILABLE"}'), 'application/json'); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return { origin: `http://127.0.0.1:${port}`, ledger, assets, graphs: graph.graphs,
    close: () => new Promise((resolve, reject) => { server.close(error => error ? reject(error) : resolve()); server.closeAllConnections(); }) };
}
