// Trusted build step only. Never executed inside the evidence worker.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import ts from 'typescript';

const root = new URL('../../../', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8').replace(/\r\n/g, '\n');
const hash = value => createHash('sha256').update(value).digest('hex');
const registryBytes = readFileSync(new URL('backend/experiments/admission_data/manifest.json', root));
if (hash(registryBytes) !== '333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699') throw Error('REGISTRY_PIN');
const registry = JSON.parse(registryBytes.toString());
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
  const source = read('frontend/src/' + path);
  const ast = ts.createSourceFile(path, source, ts.ScriptTarget.ES2022, true);
  for (const name of names) {
    const found = ast.statements.filter(s => s.name?.text === name ||
      ts.isVariableStatement(s) && s.declarationList.declarations.some(d => d.name.getText(ast) === name));
    if (found.length !== 1) throw Error('DECLARATION_PIN');
    declarations.push(found[0].getText(ast).replace(/^export /, ''));
  }
}
// Pinned dependency's self-contained distribution; no require/import/dynamic code.
const psl = read('frontend/node_modules/tldts/dist/index.cjs.min.js');
const ast = ts.createSourceFile('psl.js', psl, ts.ScriptTarget.ES2022, true, ts.ScriptKind.JS);
function check(node) {
  if (ts.isImportDeclaration(node) || ts.isCallExpression(node) &&
      ['require', 'eval', 'Function', 'import'].includes(node.expression.getText(ast))) throw Error('DEPENDENCY_CAPABILITY');
  ts.forEachChild(node, check);
}
check(ast);
const lock = readFileSync(new URL('frontend/package-lock.json', root));
const packages = JSON.parse(lock.toString()).packages;
if (process.versions.node !== '22.15.0' || ts.version !== '5.9.3' || packages['node_modules/tldts'].version !== '7.5.5') throw Error('TOOLCHAIN_PIN');
const pure = ts.transpileModule(declarations.join('\n'), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None }, reportDiagnostics: true,
});
if (pure.diagnostics?.some(d => d.category === ts.DiagnosticCategory.Error)) throw Error('TRANSPILE_FAILED');
const code = `'use strict';\nconst parseDomain = (() => { const exports = {};\n${psl}\nreturn exports.parse; })();\n${pure.outputText}\n`;
const worker = code + read('frontend/scripts/shared-rules/worker.mjs');
const provenance = { schema: 'phase6c03-rule-artifact-v1', node: process.versions.node,
  typescript: ts.version, tldts: packages['node_modules/tldts'].version,
  lock_sha256: hash(lock), registry_sha256: hash(registryBytes),
  engine_sha256: registry.engine_sha256, selections,
  psl_sha256: hash(psl), worker_sha256: hash(worker) };
const output = new URL('.local/phase6c03-build/', root);
mkdirSync(output, { recursive: true });
writeFileSync(new URL('worker.mjs', output), worker);
writeFileSync(new URL('provenance.json', output), JSON.stringify(provenance, null, 2) + '\n');
console.log('Built pinned pure rules:', provenance.worker_sha256);
