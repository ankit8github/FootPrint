/** Serial cold Chromium measurements; app and worker deadlines are never patched. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { gzipSync } from 'node:zlib';
import { chromium } from 'playwright';
import { root } from './build.mjs';
import { installProbe } from './probe.mjs';

export const protocol = Object.freeze({ iterations: 30, cpuRate: 4, latency: 150,
  downloadThroughput: 200000, uploadThroughput: 93750, gzipLevel: 6,
  mobile: { width: 390, height: 844 }, desktop: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const readyText = { '/': 'Understand your digital relationships.', '/phase5': 'Review your fictional footprint.' };
const sources = ['emails/registration-shop.eml', 'emails/receipt-shop.eml', 'history/core.json'].map(name => path.join(root, 'tests/fixtures/pv1/v1', name));
const secret = text => /SYNTHETIC_(?:BODY|FILENAME|NOT_A|USER|FRAGMENT|ATTACHMENT)|synthetic-person-01@person\.test|Browser History|From: Fictional/u.test(text);
export async function measure(server, { route, viewport, iteration, output, trace = false, interactions = true, assertLazy = false }) {
  const browser = await chromium.launch({ headless: true });
  const startLedger = server.ledger.length;
  const violations = [], requests = [], workerURLs = [];
  let phase = 'initial';
  try {
    const context = await browser.newContext({ viewport: protocol[viewport], deviceScaleFactor: 1, serviceWorkers: 'block' });
    const allowed = new Set([...server.assets.map(a => '/' + a.file), '/', '/phase2', '/phase3', '/phase4', '/phase5', '/api/v1/demo', '/favicon.ico']);
    await context.route('**/*', async interception => {
      const request = interception.request(), url = new URL(request.url());
      if (url.origin !== server.origin || url.search || !allowed.has(url.pathname) || request.method() !== 'GET') {
        violations.push('UNEXPECTED_REQUEST'); await interception.abort(); return;
      }
      if (secret(request.url() + JSON.stringify(request.headers()) + (request.postData() ?? ''))) violations.push('REQUEST_SECRET');
      await interception.continue();
    });
    context.on('request', request => requests.push({ request, phase }));
    const page = await context.newPage();
    page.on('console', message => { if (secret(message.text())) violations.push('CONSOLE_SECRET'); if (message.type() === 'error') violations.push('CONSOLE_ERROR'); });
    page.on('pageerror', () => violations.push('PAGE_ERROR'));
    page.on('websocket', () => violations.push('WEBSOCKET'));
    page.on('worker', worker => workerURLs.push({ path: new URL(worker.url()).pathname, phase }));
    await page.addInitScript(installProbe);
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.clearBrowserCache');
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: protocol.latency,
      downloadThroughput: protocol.downloadThroughput, uploadThroughput: protocol.uploadThroughput, connectionType: 'cellular3g' });
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: protocol.cpuRate });
    await cdp.send('Performance.enable');
    const events = [];
    cdp.on('Tracing.dataCollected', data => events.push(...data.value));
    await cdp.send('Tracing.start', { categories: 'devtools.timeline,v8,disabled-by-default-v8.compile', transferMode: 'ReportEvents' });
    await page.goto(server.origin + route, { waitUntil: 'networkidle', timeout: 30000 });
    await page.getByRole('heading', { name: readyText[route], exact: true }).waitFor({ state: 'visible', timeout: 15000 });
    if (route === '/') await page.getByText('Local API connected · empty demo contract', { exact: true }).waitFor({ timeout: 15000 });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const initial = await page.evaluate(() => ({ lcp: window.__fpPerf.lcp, workers: window.__fpPerf.workers.length,
      navigation: performance.getEntriesByType('navigation')[0].toJSON(),
      paints: performance.getEntriesByType('paint').map(e => ({ name: e.name, ms: e.startTime })),
      longTasks: window.__fpPerf.longTasks.slice(), resources: performance.getEntriesByType('resource').map(e => e.toJSON()) }));
    const metrics = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
    const endTrace = new Promise(resolve => cdp.once('Tracing.tracingComplete', resolve));
    await cdp.send('Tracing.end'); await endTrace;
    const compile = events.filter(e => e.ph === 'X' && /(?:v8\.compile|V8\.Compile|V8\.Parse)/u.test(e.name));
    const compileByName = {};
    for (const event of compile) compileByName[event.name] = (compileByName[event.name] ?? 0) + (event.dur ?? 0) / 1000;
    if (trace) await fs.writeFile(path.join(output, `${viewport}-${route === '/' ? 'root' : 'phase5'}-initial-trace.json.gz`), gzipSync(JSON.stringify({ traceEvents: events })));
    assert(initial.lcp && initial.lcp.ms > 0, 'LCP unavailable');
    assert.equal(initial.workers, 0, 'Worker created before selection');
    assert.equal(workerURLs.length, 0, 'Worker target before selection');
    assert.equal(requests.filter(r => r.request.url().includes('.worker-')).length, 0, 'Worker script before selection');
    const initialLedger = server.ledger.length;
    if (trace) await page.screenshot({ path: path.join(output, `${viewport}-${route === '/' ? 'root' : 'phase5'}-initial.png`), fullPage: true });
    async function operation(name, action) {
      phase = name;
      await page.evaluate(name => window.__fpPerf.arm(name), name);
      await action();
      await page.waitForFunction(() => window.__fpPerf.pending?.done !== null, null, { timeout: 15000 });
    }
    if (route === '/phase5' && interactions) {
      await page.getByRole('checkbox').check();
      await operation('selection', () => page.getByLabel('Select synthetic MVP files').setInputFiles(sources));
      await operation('filter', () => page.getByLabel('Review priority', { exact: true }).selectOption('sensitive'));
      await page.getByLabel('Review priority', { exact: true }).selectOption('all');
      await operation('disclosure', () => page.locator('.finding').first().locator('summary').click());
      await operation('recompute', () => page.getByRole('button', { name: 'Remove Source 2', exact: true }).click());
      assert.equal(await page.locator('.finding').count(), 3);
    }
    const final = await page.evaluate(async () => ({ operations: window.__fpPerf.operations,
      workers: window.__fpPerf.workers, storage: { local: Object.keys(localStorage).length, session: Object.keys(sessionStorage).length,
        databases: (await indexedDB.databases()).length, serviceWorkers: (await navigator.serviceWorker.getRegistrations()).length } }));
    assert.deepEqual(final.storage, { local: 0, session: 0, databases: 0, serviceWorkers: 0 });
    assert.equal((await context.cookies()).length, 0);
    if (route === '/phase5' && interactions) {
      assert.equal(final.workers.length, 2); assert(final.workers.every(w => w.terminated !== null));
      assert.equal(final.operations.length, 4);
    }
    const waterfall = [];
    for (const { request, phase: stage } of requests) {
      const response = await request.response();
      assert(response && response.status() < 400, 'Failed HTTP response');
      await response.finished();
      let sizes = null;
      try { sizes = await request.sizes(); } catch { /* Explicitly unverified if Chromium cannot expose worker sizes. */ }
      const url = new URL(request.url());
      waterfall.push({ path: url.pathname, phase: stage, type: request.resourceType(), status: response.status(),
        timing: request.timing(), sizes, encoding: response.headers()['content-encoding'] ?? 'identity' });
    }
    const ledger = server.ledger.slice(startLedger);
    assert(ledger.every(r => r.completed), 'Incomplete response body accounting');
    assert.deepEqual(violations, [], 'Privacy/runtime guard failed');
    const initialPaths = [...new Set(waterfall.filter(r => r.phase === 'initial' && r.path.endsWith('.js')).map(r => r.path))];
    const js = initialPaths.map(p => server.assets.find(a => '/' + a.file === p));
    assert(js.every(Boolean));
    // Chromium reports zero encoded bytes for dedicated-worker scripts in this
    // runner. Check against actual served gzip bodies instead of calling that 0.
    const served = new Map();
    for (const record of ledger) {
      const entries = served.get(record.path) ?? [];
      entries.push(record); served.set(record.path, entries);
    }
    for (const row of waterfall) {
      const record = served.get(row.path)?.shift();
      row.servedBodyBytes = record?.bodyBytes ?? null;
      row.sizeVerified = row.sizes !== null && row.sizes.responseBodySize === row.servedBodyBytes;
    }
    assert.equal(waterfall.filter(r => r.path === '/api/v1/demo').length, route === '/' ? 1 : 0, 'Unexpected or duplicate API fetch');
    if (assertLazy) {
      const modules = server.graphs.filter(g => g.realm === 'page').flatMap(g => g.chunks)
        .filter(chunk => initialPaths.includes('/' + chunk.file)).flatMap(chunk => chunk.modules).map(m => m.id);
      assert(modules.length > 0, 'Missing page graph');
      if (route === '/') assert(!modules.some(id => id.startsWith('src/features/')), 'Root fetched feature modules');
      else assert(!modules.some(id => /\/(ImportLab|EvidenceLab|AssessmentLab)\.tsx$/u.test(id)), 'Unused lab component fetched');
    }
    const sizeCoverage = waterfall.every(r => r.sizeVerified);
    return { route, viewport, iteration, browser: browser.version(), initial, metrics,
      compileEventsInclusiveMs: Object.keys(compileByName).length ? compileByName : null,
      initialJSBytes: js.reduce((n, a) => n + a.bytes, 0), initialJSGzipBytes: js.reduce((n, a) => n + a.gzipBytes, 0),
      httpBodyBytes: ledger.reduce((n, r) => n + r.bodyBytes, 0), initialHttpBodyBytes: server.ledger.slice(startLedger, initialLedger).reduce((n, r) => n + r.bodyBytes, 0),
      totalHTTPBytes: ledger.reduce((n, r) => n + r.socketReadBytes + r.socketWrittenBytes, 0),
      browserReportedHTTPBytes: sizeCoverage ? waterfall.reduce((n, r) => n + Object.values(r.sizes).reduce((a, b) => a + b, 0), 0) : null,
      totalHTTPBytesLowerBound: waterfall.reduce((n, r) => n + (r.sizeVerified ? Object.values(r.sizes).reduce((a, b) => a + b, 0) : r.servedBodyBytes ?? 0), 0),
      waterfall, serverLedger: ledger, workerURLs, final, violations };
  } finally { await browser.close(); }
}
