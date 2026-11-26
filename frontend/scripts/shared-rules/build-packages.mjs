// Additive implementation revisions; no historical source or registry writes.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import ts from 'typescript';
import { indexed } from './indexing-transforms.mjs';

const root = new URL('../../../', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8').replace(/\r\n/g, '\n');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const registry = readFileSync(new URL('backend/experiments/admission_data/manifest.json', root));
if (hash(registry) !== '333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699') throw Error('REGISTRY_PIN');
const manifest = JSON.parse(registry);
for (const [path, digest] of Object.entries(manifest.engine_sha256)) {
  if (hash(read('frontend/src/' + path)) !== digest) throw Error('ENGINE_PIN');
}
const selections = {
  'features/discovery/discovery.ts': ['linkEvidence'],
  'features/assessments/assessments.ts': ['safeEventId', 'has', 'commercial', 'matches', 'result', 'assessDiscovery'],
  'features/imports/parsers.ts': ['registrableDomain'],
  'features/assessments/explanations.ts': ['EXPLANATIONS', 'LIMITATIONS', 'RATIONALES'],
};
function declarations(path, names) {
  const ast = ts.createSourceFile(path, read('frontend/src/' + path), ts.ScriptTarget.ES2022, true);
  return names.map(name => {
    const found = ast.statements.filter(s => s.name?.text === name || ts.isVariableStatement(s) &&
      s.declarationList.declarations.some(d => d.name.getText(ast) === name));
    if (found.length !== 1) throw Error('DECLARATION_PIN');
    return found[0].getText(ast).replace(/^export /, '');
  }).join('\n');
}
const source = Object.entries(selections).map(([path, names]) => declarations(path, names)).join('\n');
const transpile = text => {
  const result = ts.transpileModule(text, { compilerOptions: {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None,
  }, reportDiagnostics: true });
  if (result.diagnostics?.some(d => d.category === ts.DiagnosticCategory.Error)) throw Error('TRANSPILE_FAILED');
  return result.outputText;
};
const lock = readFileSync(new URL('frontend/package-lock.json', root));
const packages = JSON.parse(lock).packages;
if (process.versions.node !== '22.15.0' || ts.version !== '5.9.3' || packages['node_modules/tldts'].version !== '7.5.5') throw Error('TOOLCHAIN_PIN');
const psl = read('frontend/node_modules/tldts/dist/index.cjs.min.js');
const prefix = `'use strict';\nconst parseDomain = (() => { const exports = {};\n${psl}\nreturn exports.parse; })();\n`;
const historicalPure = prefix + transpile(source) + '\n';
if (hash(historicalPure) !== '73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5') throw Error('HISTORICAL_PIN');
const historical = historicalPure + read('frontend/scripts/shared-rules/worker.mjs');
if (hash(historical) !== '69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064') throw Error('HISTORICAL_WORKER_PIN');
const actionSource = declarations('features/actions/directory.ts', ['ACTION_DIRECTORY', 'actionsFor']);
const optimizedPure = prefix + transpile(indexed(source)) + '\n';
if (hash(optimizedPure) !== '5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7') throw Error('INDEXED_PIN');
const optimized = optimizedPure + transpile(actionSource) + read('frontend/scripts/shared-rules/package-worker.mjs');
const inputs = ['frontend/scripts/shared-rules/build-packages.mjs',
  'frontend/scripts/shared-rules/package-worker.mjs', 'frontend/scripts/shared-rules/indexing-transforms.mjs',
  'frontend/src/features/actions/directory.ts', 'backend/experiments/minimized_contract.py',
  'backend/experiments/indexing_validation.py'];
const provenance = { schema: 'phase6c03-implementation-packages-v1',
  semantic_registry_sha256: hash(registry), semantic_versions: {
    schema: 'minimized-evidence-v1', parser: 'phase2-normalized-v1', feature: 'email_features_v1',
    fusion: 'relationship_fusion_v1', context: 'email_context_v1', assessment: 'sensitivity_rules_v1',
  }, engine_sha256: manifest.engine_sha256, selections, node: process.versions.node,
  typescript: ts.version, tldts: packages['node_modules/tldts'].version,
  normalized_lock_sha256: hash(lock.toString('utf8').replace(/\r\n/g, '\n')),
  psl_sha256: hash(psl), source_sha256: Object.fromEntries(inputs.map(path => [path, hash(read(path))])),
  packages: { 'historical-v1': { worker_sha256: hash(historical), pure_sha256: hash(historicalPure),
    validator: 'MinimizedBatch', historical_source_head: '580fddd8f081182a21bde60eb24d26005115e47f' },
  'indexed-r1': { worker_sha256: hash(optimized), pure_sha256: hash(optimizedPure),
    validator: 'IndexedBatch', equivalent_to: 'historical-v1' } }, synthetic_only: true };
const output = new URL('.local/phase6c03-packages/', root);
for (const [revision, worker, pure] of [['historical-v1', historical, historicalPure], ['indexed-r1', optimized, optimizedPure]]) {
  const directory = new URL(revision + '/', output);
  mkdirSync(directory, { recursive: true });
  writeFileSync(new URL('worker.mjs', directory), worker);
  writeFileSync(new URL('pure.mjs', directory), pure + 'export { linkEvidence, assessDiscovery };\n');
}
writeFileSync(new URL('candidate-manifest.json', output), JSON.stringify(provenance, null, 2) + '\n');
console.log(JSON.stringify(provenance));
