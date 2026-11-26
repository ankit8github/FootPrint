// Measurement-only wrapper: no raw reader, network, DB, profiler files or inspector.
/* global linkEvidence, assessDiscovery */
import { readSync, writeSync } from 'node:fs';

const origin = performance.now();
let previous = origin;
let previousCPU = process.cpuUsage();
function mark(phase, extra = {}) {
  const now = performance.now(), cpu = process.cpuUsage();
  writeSync(2, JSON.stringify({ phase, elapsed_ms: now - origin, wall_ms: now - previous,
    cpu_ms: (cpu.user + cpu.system - previousCPU.user - previousCPU.system) / 1000,
    peak_rss_kib: process.resourceUsage().maxRSS, ...extra }) + '\n');
  previous = now; previousCPU = cpu;
}
mark('entered');
// EXACT_PINNED_PURE_DECLARATIONS
mark('rules_loaded');
try {
  const chunks = [];
  let size = 0;
  for (;;) {
    const block = Buffer.alloc(65536);
    const length = readSync(0, block, 0, block.length, null);
    if (!length) break;
    size += length;
    if (size > 8 * 1024 * 1024) throw Error();
    chunks.push(block.subarray(0, length));
  }
  mark('read', { input_bytes: size });
  const batch = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  mark('parse');
  const observations = batch.observations.map(o => ({ ...o, evidence_state: 'observed' }));
  mark('prepare');
  const discovery = linkEvidence(batch.sources, observations, batch.excluded);
  mark('link');
  const assessments = assessDiscovery(discovery, batch.contexts);
  mark('assess');
  const result = { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1',
    context_version: 'email_context_v1', synthetic_only: true, discovery,
    context_evidence: batch.contexts, assessments };
  mark('assemble');
  const output = Buffer.from(JSON.stringify({ result, peak_rss_kib: process.resourceUsage().maxRSS }));
  mark('serialize', { output_bytes: output.length });
  if (output.length > 32 * 1024 * 1024) throw Error();
  writeSync(1, output);
  mark('write');
} catch {
  mark('failed');
  process.exitCode = 1;
}
