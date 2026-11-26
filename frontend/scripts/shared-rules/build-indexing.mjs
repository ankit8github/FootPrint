// New trusted experiment builder. Reads protected files; writes only new artifacts.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import ts from 'typescript';
import { indexed, replacements } from './indexing-transforms.mjs';

const root = new URL('../../../', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8').replace(/\r\n/g, '\n');
const hash = value => createHash('sha256').update(value).digest('hex');
const registryBytes = readFileSync(new URL('backend/experiments/admission_data/manifest.json', root));
if (hash(registryBytes) !== '333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699') throw Error('REGISTRY_PIN');
const registry = JSON.parse(registryBytes);
for (const [path, digest] of Object.entries(registry.engine_sha256)) {
  if (hash(read('frontend/src/' + path)) !== digest) throw Error('ENGINE_PIN');
}
const selections = {
  'features/discovery/discovery.ts': ['linkEvidence'],
  'features/assessments/assessments.ts': ['safeEventId', 'has', 'commercial', 'matches', 'result', 'assessDiscovery'],
  'features/imports/parsers.ts': ['registrableDomain'],
  'features/assessments/explanations.ts': ['EXPLANATIONS', 'LIMITATIONS', 'RATIONALES'],
};
const declarations = [];
for (const [path, names] of Object.entries(selections)) {
  const ast = ts.createSourceFile(path, read('frontend/src/' + path), ts.ScriptTarget.ES2022, true);
  for (const name of names) {
    const found = ast.statements.filter(s => s.name?.text === name || ts.isVariableStatement(s) &&
      s.declarationList.declarations.some(d => d.name.getText(ast) === name));
    if (found.length !== 1) throw Error('DECLARATION_PIN');
    declarations.push(found[0].getText(ast).replace(/^export /, ''));
  }
}
const original = readFileSync(new URL('.local/phase6c03-build/worker.mjs', root));
if (hash(original) !== '69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064') throw Error('ORIGINAL_ARTIFACT_PIN');
const oldWrapper = read('frontend/scripts/shared-rules/worker.mjs');
const originalText = original.toString();
if (!originalText.endsWith(oldWrapper)) throw Error('WRAPPER_PIN');
const purePrefix = originalText.slice(0, -oldWrapper.length);
const baselineSource = declarations.join('\n');
const lock = readFileSync(new URL('frontend/package-lock.json', root));
const packages = JSON.parse(lock).packages;
if (process.versions.node !== '22.15.0' || ts.version !== '5.9.3' || packages['node_modules/tldts'].version !== '7.5.5') throw Error('TOOLCHAIN_PIN');
const wrapper = read('frontend/scripts/shared-rules/investigation-worker.mjs');
for (const variant of ['baseline', 'indexed']) {
  const source = variant === 'baseline' ? baselineSource : indexed(baselineSource);
  const transpile = value => ts.transpileModule(value, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None }, reportDiagnostics: true,
  });
  const baseline = transpile(baselineSource), alternative = transpile(source);
  if ([baseline, alternative].some(p => p.diagnostics?.some(d => d.category === ts.DiagnosticCategory.Error))) throw Error('TRANSPILE_FAILED');
  if (!purePrefix.endsWith(baseline.outputText + '\n')) throw Error('PURE_PREFIX_PIN');
  const code = purePrefix.slice(0, -baseline.outputText.length - 1) + alternative.outputText + '\n';
  if (variant === 'baseline' && hash(code) !== '73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5') throw Error('BASELINE_PURE_PIN');
  const worker = wrapper.replace('// EXACT_PINNED_PURE_DECLARATIONS', code);
  const output = new URL(`.local/phase6c03-indexing-build/${variant}/`, root);
  mkdirSync(output, { recursive: true });
  writeFileSync(new URL('worker.mjs', output), worker);
  writeFileSync(new URL('pure.mjs', output), code + 'export { linkEvidence, assessDiscovery };\n');
  const types = `import type { DiscoveryGraph, EvidenceObservation, EvidenceSource, ExcludedRecord, Relationship } from '../../../frontend/src/features/discovery/types';
import type { Assessment, ContextEvidence, Limitation, Priority, RationaleCode, Rule } from '../../../frontend/src/features/assessments/types';
import { parse as parseDomain } from '../../../frontend/node_modules/tldts';\n`;
  writeFileSync(new URL('copy.ts', output), types + source);
  writeFileSync(new URL('provenance.json', output), JSON.stringify({ variant,
    node: process.versions.node, typescript: ts.version, tldts: packages['node_modules/tldts'].version,
    registry_sha256: hash(registryBytes), lock_sha256: hash(lock), engine_sha256: registry.engine_sha256,
    original_worker_sha256: hash(original), pure_sha256: hash(code), worker_sha256: hash(worker),
    transforms: variant === 'indexed' ? replacements : [], experimental_only: true,
  }, null, 2) + '\n');
  console.log('Separate', variant, 'artifact:', hash(worker));
}
