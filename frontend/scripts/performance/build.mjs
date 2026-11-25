/** Observation-only production build graph. Never imported by the application. */
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { build } from 'vite';

export const root = fileURLToPath(new URL('../../../', import.meta.url));
export const frontend = path.join(root, 'frontend');
export const relative = id => id.replaceAll('\\', '/').replace(frontend.replaceAll('\\', '/') + '/', '').replace(root.replaceAll('\\', '/') + '/', 'repo/');
export async function inventory(directory) {
  const result = [];
  async function walk(folder) {
    for (const entry of await fs.readdir(folder, { withFileTypes: true })) {
      const filename = path.join(folder, entry.name);
      if (entry.isDirectory()) await walk(filename);
      else {
        const buffer = await fs.readFile(filename);
        result.push({ file: path.relative(directory, filename).replaceAll('\\', '/'), bytes: buffer.length,
          gzipBytes: gzipSync(buffer, { level: 6 }).length, sha256: createHash('sha256').update(buffer).digest('hex') });
      }
    }
  }
  await walk(directory);
  return result.sort((a, b) => a.file.localeCompare(b.file));
}
export async function archiveGraph(directory, { ordinary } = {}) {
  const graphs = [];
  const audit = realm => ({
    name: 'footprint-observe-production-graph',
    generateBundle(_options, bundle) {
      const chunks = Object.values(bundle).filter(item => item.type === 'chunk').map(chunk => ({
        file: chunk.fileName, entry: chunk.isEntry, dynamicEntry: chunk.isDynamicEntry,
        imports: chunk.imports, dynamicImports: chunk.dynamicImports,
        modules: Object.entries(chunk.modules).map(([id, module]) => ({ id: relative(id), renderedLength: module.renderedLength })),
      }));
      const modules = [...this.getModuleIds()].map(id => {
        const info = this.getModuleInfo(id);
        return { id: relative(id), imports: info.importedIds.map(relative), dynamicImports: info.dynamicallyImportedIds.map(relative) };
      });
      graphs.push({ realm, chunks, modules });
    },
  });
  await build({ root: frontend, configFile: path.join(frontend, 'vite.config.ts'),
    plugins: [audit('page')], worker: { plugins: () => [audit('worker')] },
    build: { outDir: directory, emptyOutDir: false } });
  const assets = await inventory(directory);
  if (ordinary) {
    const expected = (await inventory(ordinary)).filter(a => /\.(js|css)$/.test(a.file));
    const actual = assets.filter(a => /\.(js|css)$/.test(a.file));
    if (JSON.stringify(expected) !== JSON.stringify(actual)) throw new Error('Observed build differs from ordinary JS/CSS build');
  }
  const record = { schema: 'footprint-build-inventory-v1', gzipLevel: 6, assets, graphs };
  await fs.writeFile(path.join(path.dirname(directory), path.basename(directory) + '-inventory.json'), JSON.stringify(record, null, 2) + '\n');
  return record;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [, , destination, ordinary] = process.argv;
  if (!destination) throw new Error('Usage: node scripts/performance/build.mjs OUT_DIR [ORDINARY_BUILD]');
  const result = await archiveGraph(path.resolve(destination), { ordinary: ordinary && path.resolve(ordinary) });
  console.log(JSON.stringify(result.assets, null, 2));
}
