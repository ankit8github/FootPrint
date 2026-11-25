import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { expect, it, vi } from 'vitest';
import { assessSelectedFiles } from '../../src/features/assessments/assessments';

const root = new URL('../../../', import.meta.url);
const corpus = new URL('tests/fixtures/pv1/v1/', root);
const output = new URL('backend/experiments/admission_data/', root);
const hash = (value: string | Uint8Array) => createHash('sha256').update(value).digest('hex');
// Git text checkouts may use CRLF on Windows. Only engine/tool source hashes use
// LF normalization; approved corpus bytes are always hashed exactly as read.
const sourceHash = (value: Uint8Array) => hash(Buffer.from(value).toString('utf8').replace(/\r\n/g, '\n'));
const corpusBytes = readFileSync(new URL('manifest.json', corpus));
// Explicit approved historical bytes, never auto-repin from an altered corpus.
const corpusPin = '53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1';
interface Source { id: string; path: string; adapter: string; sha256: string }
interface Selection { id: string; sources: string[]; after_delete: { delete_sources: string[] }[] }
// Only selection metadata is used. Expected labels are never read as engine rules.
const manifest = JSON.parse(corpusBytes.toString('utf8')) as { sources: Source[]; cases: Selection[] };
const sourceById = new Map(manifest.sources.map(s => [s.id, s]));
const modules = ['features/imports/parsers.ts', 'features/imports/approved-sources.json',
  'features/discovery/discovery.ts', 'features/discovery/types.ts',
  'features/assessments/assessments.ts', 'features/assessments/types.ts',
  'features/assessments/explanations.ts', 'phase2.generated.ts'];
function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{' + Object.entries(value)
    .sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
    .map(([k, v]) => JSON.stringify(k) + ':' + canonical(v)).join(',') + '}';
  const text = JSON.stringify(value);
  if (text === undefined || /[^\x20-\x7e]/.test(text)) throw new Error('Noncanonical scalar');
  return text;
}

it('reproduces complete registered profiles from exact gated bytes, without network or oracle rules', async () => {
  vi.stubGlobal('fetch', () => { throw new Error('Offline only'); });
  vi.stubGlobal('WebSocket', class { constructor() { throw new Error('Offline only'); } });
  try {
    expect(hash(corpusBytes)).toBe(corpusPin);
    expect(manifest.cases).toHaveLength(29);
    const selections = manifest.cases.flatMap(c => [{ id: c.id, sources: c.sources },
      ...c.after_delete.map((d, i) => ({ id: `${c.id}-d${i + 1}`,
        sources: c.sources.filter(s => !d.delete_sources.includes(s)) }))]);
    expect(selections).toHaveLength(35);
    const profiles = [], entries = new Map<string, string>(), domains = new Set<string>();
    for (const selection of selections.flatMap(s => [s, { id: s.id + '-reverse', sources: [...s.sources].reverse() }])) {
      const selected = selection.sources.map(id => {
        const source = sourceById.get(id);
        if (!source) throw new Error('Missing selection');
        const bytes = readFileSync(new URL(source.path, corpus));
        expect(hash(bytes)).toBe(source.sha256);
        return { source, file: new File([bytes], source.path.split('/').at(-1)!) };
      });
      const result = await assessSelectedFiles(selected.map(s => s.file));
      const graph = result.discovery;
      const observations = graph.observations.map(({ evidence_state, ...observation }) => {
        expect(evidence_state).toBe('observed');
        if (observation.domain) domains.add(observation.domain);
        return observation;
      });
      const aliases = [...new Set(observations.flatMap(o => o.order_keys))];
      const commercial_groups = aliases.map(alias => {
        const members = observations.filter(o => o.order_keys.includes(alias));
        expect(members.length).toBeGreaterThan(0);
        expect(members[0].domain).not.toBeNull();
        expect(members.every(o => o.domain === members[0].domain)).toBe(true);
        return { alias, domain: members[0].domain, members: members.map(o => o.id) };
      });
      const batch = { schema_version: 'minimized-evidence-v1', parser_version: 'phase2-normalized-v1',
        feature_version: graph.feature_version, fusion_version: graph.ruleset_version,
        context_version: result.context_version, assessment_version: result.ruleset_version,
        sources: graph.sources, observations, excluded: graph.excluded,
        duplicate_groups: graph.duplicate_groups, commercial_groups,
        contexts: result.context_evidence.filter(c => c.features.length > 0) };
      const bytes = canonical(batch), digest = hash(bytes);
      expect(bytes).not.toMatch(/https?:|@|SYNTHETIC-ORDER|SYNTHETIC-INVOICE|message-id|raw_body/i);
      entries.set(digest, bytes + '\n');
      profiles.push({ id: selection.id, sources: selected.map(({ source }) => ({
        id: source.id, path: source.path, adapter: source.adapter, sha256: source.sha256 })), digest,
        discovery_sha256: hash(canonical(graph)), assessment_sha256: hash(canonical(result)) });
    }
    const locked = JSON.parse(readFileSync(new URL('frontend/package-lock.json', root), 'utf8')) as {
      packages: Record<string, { version: string }> };
    const registry = { schema_version: 'minimized-registry-v1', corpus_sha256: corpusPin,
      generator_version: 'minimized-projection-v1',
      generator_sha256: sourceHash(readFileSync(new URL(import.meta.url))),
      engine_hash_policy: 'utf8-crlf-to-lf-only',
      lock_sha256: sourceHash(readFileSync(new URL('frontend/package-lock.json', root))),
      toolchain: { node: process.versions.node, vite: locked.packages['node_modules/vite'].version,
        vitest: locked.packages['node_modules/vitest'].version, tldts: locked.packages['node_modules/tldts'].version },
      engine_sha256: Object.fromEntries(modules.map(m => [m, sourceHash(readFileSync(new URL('frontend/src/' + m, root)))])),
      domains: [...domains].sort(), profiles,
      entries: [...entries].sort(([a], [b]) => a < b ? -1 : 1).map(([digest, bytes]) => ({ digest, bytes: Buffer.byteLength(bytes) - 1 })) };
    const expected = new Map([...entries].map(([digest, bytes]) => [digest + '.json', bytes]));
    expected.set('manifest.json', canonical(registry) + '\n');
    if (process.env.PV1_ADMISSION_WRITE === '1') mkdirSync(output, { recursive: true });
    for (const [name, bytes] of expected) {
      if (process.env.PV1_ADMISSION_WRITE === '1') writeFileSync(new URL(name, output), bytes);
      expect(readFileSync(new URL(name, output), 'utf8')).toBe(bytes);
    }
    expect(readdirSync(output).filter(name => /^[a-f0-9]{64}\.json$/.test(name)).sort())
      .toEqual([...entries.keys()].map(k => k + '.json').sort());
    console.log(`Registry: ${profiles.length} profiles, ${entries.size} complete batches; manifest SHA-256 ${hash(canonical(registry) + '\n')}`);
  } finally { vi.unstubAllGlobals(); }
});
