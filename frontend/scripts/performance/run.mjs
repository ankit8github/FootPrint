/** Reproduce a full 120-sample stage; results stay in the explicit local output. */
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { root } from './build.mjs';
import { measure, protocol } from './browser.mjs';
import { productionServer } from './server.mjs';

const require = createRequire(import.meta.url);
const [, , directory, outputPath, countValue = '30'] = process.argv;
if (!directory || !outputPath) throw new Error('Usage: node scripts/performance/run.mjs DIST OUTPUT [ITERATIONS=30]');
const count = Number(countValue);
assert(Number.isInteger(count) && count >= 1 && count <= 30);
const output = path.resolve(outputPath);
await fs.mkdir(output, { recursive: true });
try { await fs.access(path.join(output, 'samples.jsonl')); throw new Error('Refusing to overwrite an existing run'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
try { await fetch('http://127.0.0.1:8000/api/v1/health', { signal: AbortSignal.timeout(500) }); throw new Error('Backend port occupied; stop it before benchmark'); }
catch (error) { if (error.message.startsWith('Backend port occupied')) throw error; }
const python = path.join(root, 'backend/.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
let backendOutput = '';
const backend = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], { cwd: path.join(root, 'backend'), windowsHide: true });
backend.stdout.on('data', data => { backendOutput += data; }); backend.stderr.on('data', data => { backendOutput += data; });
let server;
try {
  let healthy = false;
  for (let i = 0; i < 100; i++) {
    if (backend.exitCode !== null) throw new Error('Benchmark backend exited: ' + backendOutput);
    try { healthy = (await fetch('http://127.0.0.1:8000/api/v1/health')).ok; } catch { /* Waiting for owned local process. */ }
    if (healthy) break;
    await delay(100);
  }
  assert(healthy, 'Backend startup failed');
  server = await productionServer(path.resolve(directory));
  const hardware = process.platform === 'win32' ? spawnSync('powershell.exe', ['-NoProfile', '-Command',
    'Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,TotalVisibleMemorySize | ConvertTo-Json'], { encoding: 'utf8', windowsHide: true }).stdout.trim() : null;
  const environment = { node: process.version, npm: spawnSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['--version'], { encoding: 'utf8', shell: process.platform === 'win32', windowsHide: true }).stdout.trim(),
    vite: require('vite/package.json').version, playwright: require('playwright/package.json').version,
    os: { platform: os.platform(), release: os.release(), arch: os.arch(), system: hardware ? JSON.parse(hardware) : null },
    hardware: { cpu: os.cpus()[0]?.model, logicalCPUs: os.cpus().length, totalRAMBytes: os.totalmem() },
    protocol: { ...protocol, iterations: count, schedule: 'serial round-robin route/viewport cells; fresh Chromium per sample' },
    instrumentation: Object.fromEntries(await Promise.all(['browser.mjs', 'probe.mjs', 'server.mjs', 'run.mjs', 'build.mjs'].map(async name => [name, createHash('sha256').update(await fs.readFile(new URL(name, import.meta.url))).digest('hex')]))),
    limitations: ['CPU emulation applied to page target; dedicated-worker CPU inheritance unverified', 'V8 compile trace durations are inclusive event sums; isolated JS syntax parse CPU unverified', 'Chromium dedicated-worker request sizes undercount bodies; total HTTP payload uses public server socket counters with one request per Connection:close connection', 'HTTP byte sizes exclude TCP/IP overhead and the local backend proxy hop; no TLS on loopback', 'OS disk cache, thermal/power state and physical mobile equivalence unverified', 'DOM input-to-two-RAF timings are lab proxies, not field INP; automation can dispatch untrusted DOM change events'] };
  await fs.writeFile(path.join(output, 'environment.json'), JSON.stringify(environment, null, 2) + '\n');
  for (let iteration = 1; iteration <= count; iteration++) {
    for (const route of ['/', '/phase5']) for (const viewport of ['mobile', 'desktop']) {
      try {
        const sample = await measure(server, { route, viewport, iteration, output, trace: iteration === 1, assertLazy: process.argv.includes('--assert-lazy') });
        await fs.appendFile(path.join(output, 'samples.jsonl'), JSON.stringify(sample) + '\n');
        console.log(JSON.stringify({ iteration, route, viewport, lcpMs: sample.initial.lcp.ms,
          initialJSGzipBytes: sample.initialJSGzipBytes, httpBodyBytes: sample.httpBodyBytes,
          operations: sample.final.operations.map(o => ({ name: o.name, ms: o.ms })) }));
      } catch (error) {
        await fs.appendFile(path.join(output, 'samples.jsonl'), JSON.stringify({ iteration, route, viewport, failed: true, error: error.message }) + '\n');
        throw error;
      }
    }
  }
  console.log('Completed all cold samples without retries.');
} finally {
  if (server) await server.close();
  backend.kill();
  if (backend.exitCode === null) await new Promise(resolve => backend.once('exit', resolve));
}
