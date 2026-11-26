// Concatenated after the exact pure declarations by build.mjs. Stdin/stdout only.
// No file paths, environment, raw parser, database or network entry points.
/* global linkEvidence, assessDiscovery */
import { readSync, writeSync } from 'node:fs';
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
  const batch = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  const discovery = linkEvidence(batch.sources, batch.observations.map(o => ({ ...o, evidence_state: 'observed' })), batch.excluded);
  const result = { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1',
    context_version: 'email_context_v1', synthetic_only: true, discovery,
    context_evidence: batch.contexts, assessments: assessDiscovery(discovery, batch.contexts) };
  const output = Buffer.from(JSON.stringify({ result, peak_rss_kib: process.resourceUsage().maxRSS }));
  if (output.length > 32 * 1024 * 1024) throw Error();
  writeSync(1, output);
} catch {
  // Never echo input, exceptions or partial JSON.
  process.exitCode = 1;
}
