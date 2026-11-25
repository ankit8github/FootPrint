/** Production loading/privacy regression checks, separate from timed 30-run evidence. */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';
import { archiveGraph, root, frontend } from './build.mjs';
import { productionServer } from './server.mjs';

const output = path.join(root, '.local/phase6b04-validation', 'check-' + Date.now());
// Explicit rollback mode checks the original eager build, not performance approval.
const baselineMode = process.argv.includes('--baseline');
const dist = path.join(output, 'dist');
await fs.mkdir(output, { recursive: true });
const build = await archiveGraph(dist, { ordinary: path.join(frontend, 'dist') });
const baseline = JSON.parse(await fs.readFile(path.join(root, 'docs/performance/phase6b04-baseline.json'), 'utf8'));
assert.deepEqual(build.assets.filter(a => a.file.includes('.worker-')), baseline.build.assets.filter(a => a.file.includes('.worker-')),
  'Worker bytes changed from the unchanged-main archive');
const pageModules = build.graphs.filter(g => g.realm === 'page').flatMap(g => g.chunks).flatMap(c => c.modules).map(m => m.id);
assert.equal(new Set(pageModules).size, pageModules.length, 'Page dependency duplicated across emitted chunks');
if (baselineMode) {
  assert.deepEqual(build.assets.filter(a => /\.(js|css)$/u.test(a.file)), baseline.build.assets.filter(a => /\.(js|css)$/u.test(a.file)),
    'Rollback JS/CSS differs from unchanged main');
  console.log('Expected rollback retained: eager loading and proposed performance budget failures remain unresolved.');
} else assert(build.assets.filter(a => a.file.endsWith('.js')).every(a => a.bytes <= 500 * 1024), 'Raw JS chunk exceeds proposed budget');
const run = spawn(process.execPath, [path.join(frontend, 'scripts/performance/run.mjs'), dist, path.join(output, 'smoke'), '1', ...(baselineMode ? [] : ['--assert-lazy'])],
  { cwd: root, stdio: 'inherit', windowsHide: true });
await new Promise((resolve, reject) => { run.once('error', reject); run.once('exit', code => code === 0 ? resolve() : reject(new Error('Production loading check failed'))); });
const samples = (await fs.readFile(path.join(output, 'smoke/samples.jsonl'), 'utf8')).trim().split('\n').map(line => JSON.parse(line));
assert.equal(samples.length, 4);
if (!baselineMode) for (const sample of samples) assert(sample.initialJSGzipBytes <= (sample.route === '/' ? 100 : 220) * 1024, 'Initial gzip JS exceeds proposed budget');

const server = await productionServer(dist);
try {
  const cases = [
    { route: '/phase2', heading: 'Import fictional evidence locally.', label: 'Select synthetic .eml or Chrome JSON', worker: 'import', done: 'Local import complete. Nothing was uploaded or saved.' },
    { route: '/phase3', heading: 'Inspect fictional evidence locally.', label: 'Select synthetic evidence files', worker: 'discovery', done: 'Local discovery complete. Nothing was uploaded or saved.' },
    { route: '/phase4', heading: 'Explain fictional review priorities.', label: 'Select synthetic assessment files', worker: 'assessment', done: 'Local assessment complete. Nothing was uploaded or saved.' },
  ];
  for (const scenario of cases) {
    const browser = await chromium.launch({ headless: true });
    try {
      const context = await browser.newContext({ serviceWorkers: 'block' });
      const page = await context.newPage(), requests = [], workers = [], errors = [];
      await context.route('**/*', async intercepted => {
        const request = intercepted.request(), url = new URL(request.url());
        if (url.origin !== server.origin || request.method() !== 'GET' || url.search ||
            !(url.pathname === scenario.route || url.pathname === '/favicon.ico' || server.assets.some(a => '/' + a.file === url.pathname))) {
          errors.push('UNEXPECTED_REQUEST'); await intercepted.abort(); return;
        }
        requests.push(url.pathname); await intercepted.continue();
      });
      page.on('pageerror', () => errors.push('PAGE_ERROR'));
      page.on('console', () => errors.push('UNEXPECTED_CONSOLE'));
      page.on('websocket', () => errors.push('WEBSOCKET'));
      page.on('worker', worker => workers.push(new URL(worker.url()).pathname));
      await page.goto(server.origin + scenario.route, { waitUntil: 'networkidle' });
      await page.getByRole('heading', { name: scenario.heading, exact: true }).waitFor();
      assert.equal(workers.length, 0);
      assert(!requests.some(p => p.includes('.worker-')));
      const chunks = build.graphs.filter(g => g.realm === 'page').flatMap(g => g.chunks).filter(c => requests.includes('/' + c.file));
      const labModules = chunks.flatMap(c => c.modules).map(m => m.id).filter(id => /\/(ImportLab|EvidenceLab|AssessmentLab|IntegratedMvp)\.tsx$/u.test(id));
      assert.equal(labModules.length, baselineMode ? 4 : 1, 'Unexpected route-module inventory');
      await page.getByRole('checkbox').check();
      await page.getByLabel(scenario.label, { exact: true }).setInputFiles(path.join(root, 'tests/fixtures/pv1/v1/emails/registration-shop.eml'));
      await page.getByText(scenario.done, { exact: true }).waitFor();
      assert.equal(workers.length, 1);
      assert(workers[0].includes('/' + scenario.worker + '.worker-'));
      assert.equal(requests.filter(p => p.includes('.worker-')).length, 1);
      assert.deepEqual(await page.evaluate(async () => ({ local: Object.keys(localStorage).length,
        session: Object.keys(sessionStorage).length, databases: (await indexedDB.databases()).length })), { local: 0, session: 0, databases: 0 });
      assert.equal((await context.cookies()).length, 0);
      assert.deepEqual(errors, []);
      console.log('PASS production isolated route and selection-only worker: ' + scenario.route);
    } finally { await browser.close(); }
  }
} finally { await server.close(); }
console.log(baselineMode ? 'PASS seven production privacy/rollback scenarios; proposed performance budgets remain FAILED.'
  : 'PASS seven production loading/privacy scenarios and static JS budgets; no CI timing budget claim.');
