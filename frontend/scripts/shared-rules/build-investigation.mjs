// Separate measurement artifact. Existing build, wrapper and pure bodies stay unchanged.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const root = new URL('../../../', import.meta.url);
const hash = value => createHash('sha256').update(value).digest('hex');
const original = readFileSync(new URL('.local/phase6c03-build/worker.mjs', root), 'utf8');
const wrapper = readFileSync(new URL('frontend/scripts/shared-rules/worker.mjs', root), 'utf8').replace(/\r\n/g, '\n');
if (hash(original) !== '69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064' ||
    !original.endsWith(wrapper) || process.versions.node !== '22.15.0') throw Error('ARTIFACT_PIN');
const pure = original.slice(0, -wrapper.length);
const measurement = readFileSync(new URL('frontend/scripts/shared-rules/investigation-worker.mjs', root), 'utf8').replace(/\r\n/g, '\n');
const marker = '// EXACT_PINNED_PURE_DECLARATIONS';
if (measurement.split(marker).length !== 2) throw Error('MEASUREMENT_MARKER');
const instrumented = measurement.replace(marker, pure);
const output = new URL('.local/phase6c03-investigation-build/', root);
mkdirSync(output, { recursive: true });
// New artifact paths only. Original worker, provenance and benchmark receipts are untouched.
writeFileSync(new URL('worker.mjs', output), instrumented);
writeFileSync(new URL('provenance.json', output), JSON.stringify({
  original_sha256: hash(original), pure_prefix_sha256: hash(pure),
  instrumentation_sha256: hash(measurement), worker_sha256: hash(instrumented),
  node: process.versions.node, phase_metrics_only_on_stderr: true,
}, null, 2) + '\n');
console.log('Separate profiling artifact:', hash(instrumented));
