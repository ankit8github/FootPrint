/** Publish synthetic numeric evidence; full traces/screenshots stay in local output. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

export function distribution(values) {
  assert(values.length > 0 && values.every(Number.isFinite));
  const sorted = values.toSorted((a, b) => a - b);
  const rank = p => sorted[Math.ceil(p * sorted.length) - 1];
  return { n: sorted.length, min: sorted[0], p50: rank(0.5), p75: rank(0.75), p95: rank(0.95), max: sorted.at(-1) };
}

const [, , directory, inventoryFile, destination] = process.argv;
if (!directory || !inventoryFile || !destination) throw new Error('Usage: node summarize.mjs RUN_DIR INVENTORY_JSON OUTPUT_JSON');
const raw = await fs.readFile(path.join(directory, 'samples.jsonl'));
const samples = raw.toString().trim().split('\n').map(line => JSON.parse(line));
assert.equal(samples.length, 120, 'A publishable stage requires all four 30-sample cells');
assert(samples.every(s => !s.failed && s.violations.length === 0));
const environment = JSON.parse(await fs.readFile(path.join(directory, 'environment.json'), 'utf8'));
const build = JSON.parse(await fs.readFile(inventoryFile, 'utf8'));
const jsTotal = (sample, field, predicate = () => true) => sample.waterfall
  .filter(r => r.path.endsWith('.js') && predicate(r))
  .reduce((n, r) => {
    const asset = build.assets.find(a => '/' + a.file === r.path);
    assert(asset, 'JS request missing from build inventory');
    return n + asset[field];
  }, 0);
const cells = [];
for (const route of ['/', '/phase5']) for (const viewport of ['mobile', 'desktop']) {
  const rows = samples.filter(s => s.route === route && s.viewport === viewport);
  assert.equal(rows.length, 30);
  assert.deepEqual(rows.map(s => s.iteration), Array.from({ length: 30 }, (_, i) => i + 1));
  const metric = fn => distribution(rows.map(fn));
  const operations = {};
  for (const name of ['selection', 'filter', 'disclosure', 'recompute']) {
    if (route === '/phase5') operations[name] = metric(s => s.final.operations.find(o => o.name === name).ms);
  }
  const initialPaths = [...new Set(rows[0].waterfall.filter(r => r.phase === 'initial').map(r => r.path))];
  const workerPaths = [...new Set(rows[0].workerURLs.map(w => w.path))];
  cells.push({ route, viewport, browser: [...new Set(rows.map(s => s.browser))], initialPaths, workerPaths,
    lcpMs: metric(s => s.initial.lcp.ms),
    fcpMs: metric(s => s.initial.paints.find(p => p.name === 'first-contentful-paint').ms),
    scriptMs: metric(s => s.metrics.ScriptDuration * 1000),
    taskMs: metric(s => s.metrics.TaskDuration * 1000),
    layoutMs: metric(s => s.metrics.LayoutDuration * 1000),
    styleMs: metric(s => s.metrics.RecalcStyleDuration * 1000),
    longTaskMs: metric(s => s.initial.longTasks.reduce((n, t) => n + t.duration, 0)),
    initialJSBytes: metric(s => s.initialJSBytes), initialJSGzipBytes: metric(s => s.initialJSGzipBytes),
    deferredJSBytes: metric(s => jsTotal(s, 'bytes', r => r.phase !== 'initial')),
    deferredJSGzipBytes: metric(s => jsTotal(s, 'gzipBytes', r => r.phase !== 'initial')),
    workerJSBytes: metric(s => jsTotal(s, 'bytes', r => r.path.includes('.worker-'))),
    workerGzipBytes: metric(s => jsTotal(s, 'gzipBytes', r => r.path.includes('.worker-'))),
    totalJSBytes: metric(s => jsTotal(s, 'bytes')), totalJSGzipBytes: metric(s => jsTotal(s, 'gzipBytes')),
    initialBodyBytes: metric(s => s.initialHttpBodyBytes), totalBodyBytes: metric(s => s.httpBodyBytes),
    totalHTTPBytes: metric(s => s.totalHTTPBytes), requests: metric(s => s.waterfall.length), operations });
}
const publishedSamples = samples.map(s => ({ iteration: s.iteration, route: s.route, viewport: s.viewport,
    lcp: s.initial.lcp, paints: s.initial.paints, metrics: Object.fromEntries(['ScriptDuration', 'TaskDuration', 'LayoutDuration', 'RecalcStyleDuration'].map(k => [k, s.metrics[k]])),
    longTasks: s.initial.longTasks, compileEventsInclusiveMs: s.compileEventsInclusiveMs,
    operations: s.final.operations, workers: s.final.workers, initialJSBytes: s.initialJSBytes,
    initialJSGzipBytes: s.initialJSGzipBytes, initialHttpBodyBytes: s.initialHttpBodyBytes,
    httpBodyBytes: s.httpBodyBytes, totalHTTPBytes: s.totalHTTPBytes,
    waterfall: s.waterfall.map(r => ({ path: r.path, phase: r.phase, type: r.type, status: r.status,
      timing: r.timing, servedBodyBytes: r.servedBodyBytes, browserBodySizeVerified: r.sizeVerified, encoding: r.encoding })) }));
const sampleFile = destination.replace(/\.json$/u, '') + '-samples.jsonl';
const publishedRaw = publishedSamples.map(s => JSON.stringify(s)).join('\n') + '\n';
const evidence = { schema: 'footprint-performance-v1', rawSamplesSHA256: createHash('sha256').update(raw).digest('hex'),
  publishedSamples: path.basename(sampleFile), publishedSamplesSHA256: createHash('sha256').update(publishedRaw).digest('hex'),
  environment, build, cells };
await fs.mkdir(path.dirname(destination), { recursive: true });
await fs.writeFile(sampleFile, publishedRaw);
await fs.writeFile(destination, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(cells, null, 2));
