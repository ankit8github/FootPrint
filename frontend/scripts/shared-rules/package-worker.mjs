// Offline indexed revision. Exact pinned pure declarations precede this wrapper.
/* global linkEvidence, assessDiscovery, actionsFor */
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
  const discovery = linkEvidence(batch.sources,
    batch.observations.map(o => ({ ...o, evidence_state: 'observed' })), batch.excluded);
  const result = { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1',
    context_version: 'email_context_v1', synthetic_only: true, discovery,
    context_evidence: batch.contexts, assessments: assessDiscovery(discovery, batch.contexts) };
  const eligible_actions = result.assessments.map(a => actionsFor(a).map(entry => entry.id));
  const encoded = JSON.stringify({ result, eligible_actions, peak_rss_kib: process.resourceUsage().maxRSS });
  const output = Buffer.from(encoded);
  if (output.length > 32 * 1024 * 1024) throw Error();
  writeSync(1, output);
  // Full-interval RSS follows serialization/write; it is not the committed-memory cap.
  writeSync(2, JSON.stringify({ peak_rss_kib: process.resourceUsage().maxRSS }) + '\n');
} catch {
  process.exitCode = 1;
}
