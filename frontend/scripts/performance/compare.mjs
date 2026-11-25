/** Evaluate proposed budgets without changing targets or discarding samples. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const [, , beforeFile, afterFile, output] = process.argv;
if (!beforeFile || !afterFile || !output) throw new Error('Usage: node compare.mjs BEFORE_JSON AFTER_JSON OUTPUT_JSON');
const before = JSON.parse(await fs.readFile(beforeFile, 'utf8'));
const after = JSON.parse(await fs.readFile(afterFile, 'utf8'));
assert.deepEqual(before.environment, after.environment, 'Before/after environment or instrumentation differs');
assert.equal(before.cells.length, 4); assert.equal(after.cells.length, 4);
const checks = [], transfers = [];
const check = (name, actual, limit) => checks.push({ name, actual, limit, pass: actual <= limit });
for (const old of before.cells) {
  const current = after.cells.find(c => c.route === old.route && c.viewport === old.viewport);
  assert(current && old.lcpMs.n === 30 && current.lcpMs.n === 30);
  const label = current.route + ' ' + current.viewport;
  check(label + ' initial gzip JS bytes', current.initialJSGzipBytes.max, (current.route === '/' ? 100 : 220) * 1024);
  check(label + ' p75 LCP ms', current.lcpMs.p75, 2500);
  for (const [name, value] of Object.entries(current.operations)) {
    const baseline = old.operations[name].p75;
    check(label + ' ' + name + ' p75 ms (10% regression)', value.p75, baseline * 1.1);
  }
  const initialChunks = after.build.graphs.filter(g => g.realm === 'page').flatMap(g => g.chunks)
    .filter(c => current.initialPaths.includes('/' + c.file));
  const modules = initialChunks.flatMap(c => c.modules).map(m => m.id);
  const unwanted = modules.filter(id => current.route === '/' ? id.startsWith('src/features/') : /\/(ImportLab|EvidenceLab|AssessmentLab)\.tsx$/u.test(id));
  check(label + ' unused route modules fetched', unwanted.length, 0);
  check(label + ' worker scripts initially fetched', current.initialPaths.filter(p => p.includes('.worker-')).length, 0);
  transfers.push({ route: current.route, viewport: current.viewport,
    initialGzipJS: { before: old.initialJSGzipBytes.p75, after: current.initialJSGzipBytes.p75 },
    deferredGzipJS: { before: old.deferredJSGzipBytes.p75, after: current.deferredJSGzipBytes.p75 },
    totalEncodedBodies: { before: old.totalBodyBytes.p75, after: current.totalBodyBytes.p75 },
    totalHTTP: { before: old.totalHTTPBytes.p75, after: current.totalHTTPBytes.p75 },
    requests: { before: old.requests.p75, after: current.requests.p75 } });
}
check('largest emitted JS chunk raw bytes (workers included)', Math.max(...after.build.assets.filter(a => a.file.endsWith('.js')).map(a => a.bytes)), 500 * 1024);
assert.deepEqual(before.build.assets.filter(a => a.file.includes('.worker-')), after.build.assets.filter(a => a.file.includes('.worker-')),
  'Worker asset changed');
const result = { schema: 'footprint-proposed-budgets-v1', approvedPolicy: false,
  pass: checks.every(c => c.pass), checks, transfers };
await fs.writeFile(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
if (!result.pass) process.exitCode = 1;
