// @vitest-environment node
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { discoverSelectedFiles } from './discovery';
import type { DiscoveryGraph } from './types';

const corpus = new URL('../../../../tests/fixtures/pv1/v1/', import.meta.url);
const manifestBytes = readFileSync(new URL('manifest.json', corpus));
interface OracleRelationship { domain: string; relationship_type: string; evidence_state: string; confidence: string; support: string[] }
interface Snapshot {
  relationships: OracleRelationship[]; unresolved: { support: string[] }[];
  excluded: string[]; duplicate_groups: string[][];
}
interface Source { id: string; path: string; events: { id: string; locator: string; expected_utc: string | null;
  disposition: string; observation_kind: string | null; domain_label: string | null; time_status: string }[] }
interface Case { id: string; sources: string[]; expected: Snapshot; after_delete: { delete_sources: string[]; expected: Snapshot }[] }
const manifest = JSON.parse(manifestBytes.toString('utf8')) as { cases: Case[]; sources: Source[] };
const sourceById = new Map(manifest.sources.map(s => [s.id, s]));
const loadFiles = (ids: string[]) => ids.map(id => {
  const source = sourceById.get(id)!;
  return new File([readFileSync(new URL(source.path, corpus))], source.path.split('/').at(-1)!);
});
const sort = <T,>(items: T[]) => items.sort((a, b) => JSON.stringify(a) < JSON.stringify(b) ? -1 : JSON.stringify(a) > JSON.stringify(b) ? 1 : 0);
function expected(snapshot: Snapshot) {
  return { relationships: sort(snapshot.relationships.map(r => ({ domain: r.domain, relationship_type: r.relationship_type,
    evidence_state: r.evidence_state, confidence: r.confidence, support: [...r.support].sort() }))),
  unresolved: sort(snapshot.unresolved.map(x => [...x.support].sort())),
  excluded: [...snapshot.excluded].sort(), duplicate_groups: sort(snapshot.duplicate_groups.map(x => [...x])) };
}
function project(graph: DiscoveryGraph, ids: string[]) {
  const lookup = new Map<string, string>();
  ids.forEach((id, index) => sourceById.get(id)!.events.forEach((event, row) => lookup.set(`s${String(index + 1).padStart(4, '0')}:r${String(row).padStart(5, '0')}`, event.id)));
  const translate = (id: string) => { const mapped = lookup.get(id); expect(mapped, 'runtime provenance must reference a selected event').toBeDefined(); return mapped!; };
  return { relationships: sort(graph.relationships.map(r => ({ domain: r.domain, relationship_type: r.relationship_type,
    evidence_state: r.evidence_state, confidence: r.confidence, support: r.support.map(translate).sort() }))),
    unresolved: sort(graph.unresolved.map(x => x.support.map(translate).sort())),
    excluded: graph.excluded.map(x => translate(x.event_id)).sort(),
    duplicate_groups: sort(graph.duplicate_groups.map(x => x.map(translate))) };
}
function assertInvariants(graph: DiscoveryGraph) {
  const byId = new Map(graph.observations.map(o => [o.id, o]));
  expect(byId.size).toBe(graph.observations.length);
  for (const r of graph.relationships) {
    expect(r.retention_status).toBe('unknown'); expect(r.data_sale_status).toBe('unknown');
    expect(r).not.toHaveProperty('review_priority'); expect(r).not.toHaveProperty('sensitivity');
    expect(r.evidence_state).toBe(r.relationship_type === 'visited' ? 'observed' : 'inferred');
    for (const id of r.support) {
      expect(byId.get(id)?.domain).toBe(r.domain);
      expect(byId.get(id)?.duplicate_of).toBeNull();
      expect(graph.relationship_evidence).toContainEqual({ relationship_id: r.id, observation_id: id, role: 'primary' });
    }
  }
  for (const link of graph.relationship_evidence) {
    expect(byId.has(link.observation_id)).toBe(true);
    expect(graph.relationships.some(r => r.id === link.relationship_id)).toBe(true);
  }
  for (const item of graph.unresolved) { expect(item.evidence_state).toBe('unknown'); expect(item.confidence).toBe('insufficient'); }
  for (const secret of ['SYNTHETIC-ORDER-001', 'SYNTHETIC-INVOICE-001', 'SYNTHETIC_NOT_A_SECRET',
    'SYNTHETIC_USER', 'SYNTHETIC_NOT_A_PASSWORD', 'An account was requested']) expect(JSON.stringify(graph)).not.toContain(secret);
  expect(JSON.stringify(graph)).not.toMatch(/https?:|@|<script|<html|token=|raw_body|filename|message-id|sender_address|review_priority/i);
}

const rows: { id: string; sources: string[]; expected: Snapshot; survivor: boolean }[] = manifest.cases.flatMap(c => [
  { id: c.id, sources: c.sources, expected: c.expected, survivor: false },
  ...c.after_delete.map((d, i) => ({ id: `${c.id}-d${i + 1}`, sources: c.sources.filter(id => !d.delete_sources.includes(id)), expected: d.expected, survivor: true })),
]);
describe('unchanged corpus 1.1.0 discovery projections', () => {
  it.each(rows)('$id matches all Phase 3 oracle fields and remaining-source provenance', async row => {
    const graph = await discoverSelectedFiles(loadFiles(row.sources));
    expect(project(graph, row.sources)).toEqual(expected(row.expected));
    assertInvariants(graph);
    expect(await discoverSelectedFiles(loadFiles(row.sources))).toEqual(graph);
    for (const [index, id] of row.sources.entries()) {
      const source = sourceById.get(id)!;
      for (const observation of graph.observations.filter(o => o.source_id === `s${String(index + 1).padStart(4, '0')}`)) {
        const event = source.events[observation.record_index];
        const timestamp = event.expected_utc;
        expect(observation.kind).toBe(event.observation_kind);
        expect(observation.time_status).toBe(event.time_status);
        if (event.disposition === 'eligible') expect(observation.domain).toBe(event.domain_label);
        expect(observation.occurred_at === null ? null : new Date(observation.occurred_at).toISOString())
          .toBe(timestamp === null ? null : new Date(timestamp).toISOString());
      }
    }
  });
  it('produces a reproducible, explicitly limited development-set measurement', async () => {
    const results: { id: string; survivor: boolean; expected: number; predicted: number; true_positive: number;
      false_positive: number; false_negative: number; exact_in_scope_match: boolean }[] = [];
    for (const row of rows) {
      const graph = await discoverSelectedFiles(loadFiles(row.sources));
      const predicted = new Set(graph.relationships.map(r => `${r.domain}/${r.relationship_type}`));
      const truth = new Set(row.expected.relationships.map(r => `${r.domain}/${r.relationship_type}`));
      const tp = [...predicted].filter(key => truth.has(key)).length;
      results.push({ id: row.id, survivor: row.survivor, expected: truth.size, predicted: predicted.size, true_positive: tp,
        false_positive: predicted.size - tp, false_negative: truth.size - tp,
        exact_in_scope_match: JSON.stringify(project(graph, row.sources)) === JSON.stringify(expected(row.expected)) });
    }
    function aggregate(survivor: boolean) {
      const selected = results.filter(x => x.survivor === survivor);
      const sum = (field: 'true_positive' | 'false_positive' | 'false_negative') => selected.reduce((n, x) => n + x[field], 0);
      const tp = sum('true_positive'), fp = sum('false_positive'), fn = sum('false_negative');
      return { snapshots: selected.length, true_positive: tp, false_positive: fp, false_negative: fn,
        precision: tp + fp ? tp / (tp + fp) : null, recall: tp + fn ? tp / (tp + fn) : null,
        exact_in_scope_matches: selected.filter(x => x.exact_in_scope_match).length };
    }
    const metrics = { schema_version: 'phase3-development-evaluation-v1', corpus_version: '1.1.0',
      oracle_sha256: createHash('sha256').update(manifestBytes).digest('hex'),
      baseline_status: 'product-owner-approved, AI-assisted baseline', independent_blind_review: false,
      measurement: 'known_synthetic_development_corpus_not_holdout_or_product_accuracy',
      relationship_key: '(snapshot_id, canonical_domain, relationship_type)',
      precision_definition: 'TP/(TP+FP), null for zero predictions', recall_definition: 'TP/(TP+FN), null for zero ground truth',
      compared_fields: ['domain', 'relationship_type', 'evidence_state', 'confidence', 'canonical_support', 'unresolved_support', 'excluded_events', 'duplicate_groups'],
      unassessed_fields: ['review_priority', 'sensitivity', 'sensitivity_agreement'],
      initial_cases: aggregate(false), survivor_oracles: aggregate(true), sensitivity_agreement: null, results };
    const target = new URL('../../../../docs/PHASE3-METRICS.json', import.meta.url);
    if (process.env.PV1_WRITE_PHASE3_METRICS === '1') writeFileSync(target, JSON.stringify(metrics, null, 2) + '\n');
    expect(metrics).toEqual(JSON.parse(readFileSync(target, 'utf8')));
  });
});
