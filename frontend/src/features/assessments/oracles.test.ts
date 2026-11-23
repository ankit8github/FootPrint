// @vitest-environment node
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { assessSelectedFiles } from './assessments';
import type { AssessmentBatch } from './types';

const corpus = new URL('../../../../tests/fixtures/pv1/v1/', import.meta.url);
const bytes = readFileSync(new URL('manifest.json', corpus));
interface ExpectedRelationship { domain: string; relationship_type: string; evidence_state: string; confidence: string;
  review_priority: string; rationale_codes: string[]; support: string[]; retention_status: string; data_sale_status: string }
interface Snapshot { relationships: ExpectedRelationship[];
  unresolved: { support: string[]; confidence: string; review_priority: string; rationale_codes: string[] }[];
  excluded: string[]; duplicate_groups: string[][] }
const manifest = JSON.parse(bytes.toString('utf8')) as { sources: { id: string; path: string; events: { id: string }[] }[];
  cases: { id: string; sources: string[]; expected: Snapshot; after_delete: { delete_sources: string[]; expected: Snapshot }[] }[] };
const sourceById = new Map(manifest.sources.map(s => [s.id, s]));
const files = (ids: string[]) => ids.map(id => { const s = sourceById.get(id)!;
  return new File([readFileSync(new URL(s.path, corpus))], s.path.split('/').at(-1)!); });
const rows = manifest.cases.flatMap(c => [{ id: c.id, sources: c.sources, expected: c.expected, survivor: false },
  ...c.after_delete.map((d, i) => ({ id: `${c.id}-d${i + 1}`, sources: c.sources.filter(s => !d.delete_sources.includes(s)), expected: d.expected, survivor: true }))]);
const sorted = <T,>(items: T[]) => items.sort((a, b) => JSON.stringify(a) < JSON.stringify(b) ? -1 : JSON.stringify(a) > JSON.stringify(b) ? 1 : 0);
function translator(ids: string[]) {
  const map = new Map<string, string>();
  ids.forEach((id, i) => sourceById.get(id)!.events.forEach((e, row) => map.set(`s${String(i + 1).padStart(4, '0')}:r${String(row).padStart(5, '0')}`, e.id)));
  return (id: string) => { expect(map.has(id)).toBe(true); return map.get(id)!; };
}
function project(batch: AssessmentBatch, ids: string[]) {
  const translate = translator(ids);
  return { assessments: sorted(batch.assessments.map(a => ({ domain: a.domain, relationship_type: a.relationship_type,
    evidence_state: a.evidence_state, confidence: a.confidence, review_priority: a.review_priority,
    rationale_codes: a.rationale_codes, support: a.support.map(translate).sort(), retention_status: a.retention_status, data_sale_status: a.data_sale_status }))),
  excluded: batch.discovery.excluded.map(e => translate(e.event_id)).sort(),
  duplicate_groups: sorted(batch.discovery.duplicate_groups.map(g => g.map(translate))) };
}
function expected(snapshot: Snapshot) {
  return { assessments: sorted([...snapshot.relationships.map(r => ({ domain: r.domain, relationship_type: r.relationship_type,
    evidence_state: r.evidence_state, confidence: r.confidence, review_priority: r.review_priority,
    rationale_codes: r.rationale_codes, support: [...r.support].sort(), retention_status: r.retention_status, data_sale_status: r.data_sale_status })),
  ...snapshot.unresolved.map(u => ({ domain: null, relationship_type: null, evidence_state: 'unknown', confidence: u.confidence,
    review_priority: u.review_priority, rationale_codes: u.rationale_codes, support: [...u.support].sort(), retention_status: 'unknown', data_sale_status: 'unknown' }))]),
  excluded: [...snapshot.excluded].sort(), duplicate_groups: sorted(snapshot.duplicate_groups.map(g => [...g])) };
}
function semantic(batch: AssessmentBatch, ids: string[]) {
  const translate = translator(ids);
  return sorted(batch.assessments.map(a => ({ domain: a.domain, type: a.relationship_type, priority: a.review_priority,
    state: a.evidence_state, confidence: a.confidence, rule: a.rule_id, reasons: a.rationale_codes, explanation: a.explanation,
    limitations: a.limitations.map(l => l.code), all_provenance: [...new Set([...a.support,
      ...batch.discovery.relationship_evidence.filter(e => e.relationship_id === a.relationship_id).map(e => e.observation_id)].map(translate))].sort() })));
}
function invariants(batch: AssessmentBatch) {
  for (const a of batch.assessments) {
    expect(a.unknown_claims).toHaveLength(7);
    expect(a.unknown_claims.every(c => c.evidence_state === 'unknown' && c.confidence === 'insufficient')).toBe(true);
    expect(a.retention_status).toBe('unknown'); expect(a.data_sale_status).toBe('unknown');
    expect(a.rationales.map(r => r.code)).toEqual(a.rationale_codes);
    for (const reason of a.rationales) {
      expect(reason.support.length).toBeGreaterThan(0);
      expect(reason.support.every(id => a.support.includes(id))).toBe(true);
      for (const id of reason.support) expect(batch.discovery.observations.some(o => o.id === id)).toBe(true);
      if (reason.code === 'HEALTH_CONTEXT') for (const id of reason.support) {
        expect(batch.context_evidence).toContainEqual({ observation_id: id, features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] });
      }
    }
  }
  const serialized = JSON.stringify(batch);
  expect(serialized).not.toMatch(/https?:|@|<script|<html|token=|raw_body|sender_address|message-id/i);
  for (const secret of ['SYNTHETIC-ORDER-001', 'SYNTHETIC-INVOICE-001', 'SYNTHETIC_NOT_A_SECRET', 'SYNTHETIC_USER',
    'SYNTHETIC_NOT_A_PASSWORD', 'An account was requested', 'An appointment-portal account was requested']) expect(serialized).not.toContain(secret);
}

describe('immutable approved Phase 1 assessment oracles', () => {
  it.each(rows)('$id preserves all priority/rationale/claim/provenance labels', async row => {
    const batch = await assessSelectedFiles(files(row.sources));
    expect(project(batch, row.sources)).toEqual(expected(row.expected)); invariants(batch);
    expect(await assessSelectedFiles(files(row.sources))).toEqual(batch);
    const reversed = [...row.sources].reverse();
    expect(semantic(await assessSelectedFiles(files(reversed)), reversed)).toEqual(semantic(batch, row.sources));
  });
  it('reproduces explicitly limited development-set agreement and Unknown measurements', async () => {
    const results: { id: string; survivor: boolean; expected: number; predicted: number; matched_priorities: number;
      unexpected: number; missing: number; unknown_expected: number; unknown_predicted: number; unknown_correct: number;
      known_correct: number; unknown_forced_low: number; exact_snapshot_match: boolean }[] = [];
    const confusion: Record<string, Record<string, number>> = Object.fromEntries(['sensitive', 'medium', 'low', 'unknown']
      .map(p => [p, Object.fromEntries(['sensitive', 'medium', 'low', 'unknown', 'missing'].map(q => [q, 0]))]));
    for (const row of rows) {
      const batch = await assessSelectedFiles(files(row.sources));
      const actual = project(batch, row.sources).assessments, truth = expected(row.expected).assessments;
      const key = (a: { domain: string | null; relationship_type: string | null; support: string[] }) => a.domain === null ? `unknown/${a.support.join(',')}` : `${a.domain}/${a.relationship_type}`;
      const predictions = new Map(actual.map(a => [key(a), a]));
      let matched = 0, missing = 0, unknownCorrect = 0, knownCorrect = 0, forcedLow = 0;
      for (const t of truth) {
        const prediction = predictions.get(key(t));
        if (!prediction) missing++;
        confusion[t.review_priority][prediction?.review_priority ?? 'missing']++;
        if (prediction?.review_priority === t.review_priority) { matched++; if (t.review_priority === 'unknown') unknownCorrect++; else knownCorrect++; }
        if (t.review_priority === 'unknown' && prediction?.review_priority === 'low') forcedLow++;
      }
      results.push({ id: row.id, survivor: row.survivor, expected: truth.length, predicted: actual.length, matched_priorities: matched,
        unexpected: actual.filter(a => !truth.some(t => key(t) === key(a))).length, missing,
        unknown_expected: truth.filter(a => a.review_priority === 'unknown').length,
        unknown_predicted: actual.filter(a => a.review_priority === 'unknown').length, unknown_correct: unknownCorrect,
        known_correct: knownCorrect, unknown_forced_low: forcedLow,
        exact_snapshot_match: JSON.stringify(project(batch, row.sources)) === JSON.stringify(expected(row.expected)) });
    }
    function aggregate(survivor: boolean) {
      const r = results.filter(x => x.survivor === survivor);
      const sum = (field: keyof Omit<typeof results[number], 'id' | 'survivor' | 'exact_snapshot_match'>) => r.reduce((n, x) => n + x[field], 0);
      const denominator = sum('expected') + sum('unexpected');
      return { snapshots: r.length, expected_assessments: sum('expected'), predicted_assessments: sum('predicted'),
        matched_priorities: sum('matched_priorities'), unexpected: sum('unexpected'), missing: sum('missing'),
        agreement: denominator ? sum('matched_priorities') / denominator : null,
        known_priority_agreement: sum('expected') - sum('unknown_expected') ? sum('known_correct') / (sum('expected') - sum('unknown_expected')) : null,
        unknown_expected: sum('unknown_expected'), unknown_predicted: sum('unknown_predicted'), unknown_correct: sum('unknown_correct'),
        unknown_rate: sum('predicted') ? sum('unknown_predicted') / sum('predicted') : null,
        unknown_forced_low: sum('unknown_forced_low'), exact_snapshot_matches: r.filter(x => x.exact_snapshot_match).length };
    }
    const metrics = { schema_version: 'phase4-development-evaluation-v1', ruleset_version: 'sensitivity_rules_v1', context_version: 'email_context_v1',
      corpus_version: '1.1.0', baseline_status: 'product-owner-approved, AI-assisted baseline', independent_blind_review: false,
      oracle_sha256: createHash('sha256').update(bytes).digest('hex'), measurement: 'known_overlapping_synthetic_development_set_not_real_world_accuracy',
      key: '(snapshot, domain, relationship_type) or (snapshot, unresolved support)',
      agreement_definition: 'matching keyed priorities / (expected items + unexpected predictions); missing items disagree; zero denominator is null',
      empty_or_excluded_snapshots: 'no assessment; excluded inputs never become Unknown or Low assessments',
      compared_fields: ['review_priority', 'rationale_codes', 'domain', 'relationship_type', 'evidence_state', 'confidence', 'support', 'retention_status', 'data_sale_status', 'excluded_events', 'duplicate_groups'],
      initial_cases: aggregate(false), survivor_oracles: aggregate(true), confusion_all_snapshots: confusion, results };
    const target = new URL('../../../../docs/PHASE4-METRICS.json', import.meta.url);
    if (process.env.PV1_WRITE_PHASE4_METRICS === '1') writeFileSync(target, JSON.stringify(metrics, null, 2) + '\n');
    expect(metrics).toEqual(JSON.parse(readFileSync(target, 'utf8')));
  });
});
