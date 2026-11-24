// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { assessSelectedFiles } from '../assessments/assessments';
import type { AssessmentBatch } from '../assessments/types';
import { actionsFor, ACTION_DIRECTORY } from '../actions/directory';
import { initialSnapshot, LocalSession } from './session';
import type { SessionSnapshot, SessionWorker } from './session';

const corpus = new URL('../../../../tests/fixtures/pv1/v1/', import.meta.url);
interface Expected { relationships: { domain: string; relationship_type: string; evidence_state: string; confidence: string;
  review_priority: string; rationale_codes: string[]; support: string[]; retention_status: string; data_sale_status: string }[];
  unresolved: { support: string[]; confidence: string; review_priority: string; rationale_codes: string[] }[];
  excluded: string[]; duplicate_groups: string[][] }
const manifest = JSON.parse(readFileSync(new URL('manifest.json', corpus), 'utf8')) as {
  sources: { id: string; path: string; events: { id: string }[] }[];
  cases: { id: string; sources: string[]; expected: Expected; after_delete: { delete_sources: string[]; expected: Expected }[] }[] };
const sourceById = new Map(manifest.sources.map(s => [s.id, s]));
const files = (ids: string[]) => ids.map(id => { const s = sourceById.get(id)!;
  return new File([readFileSync(new URL(s.path, corpus))], s.path.split('/').at(-1)!); });
const sorted = <T,>(values: T[]) => values.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
function project(batch: AssessmentBatch, ids: string[]) {
  const map = new Map<string, string>();
  ids.forEach((id, index) => sourceById.get(id)!.events.forEach((e, row) => map.set(`s${String(index + 1).padStart(4, '0')}:r${String(row).padStart(5, '0')}`, e.id)));
  const translate = (id: string) => { expect(map.has(id)).toBe(true); return map.get(id)!; };
  return { assessments: sorted(batch.assessments.map(a => ({ domain: a.domain, type: a.relationship_type, state: a.evidence_state,
    confidence: a.confidence, priority: a.review_priority, reasons: a.rationale_codes, support: a.support.map(translate).sort(),
    retention: a.retention_status, sale: a.data_sale_status }))),
  excluded: batch.discovery.excluded.map(e => translate(e.event_id)).sort(),
  duplicates: sorted(batch.discovery.duplicate_groups.map(g => g.map(translate).sort())) };
}
function expected(snapshot: Expected) {
  return { assessments: sorted([...snapshot.relationships.map(r => ({ domain: r.domain, type: r.relationship_type, state: r.evidence_state,
    confidence: r.confidence, priority: r.review_priority, reasons: r.rationale_codes, support: [...r.support].sort(), retention: r.retention_status, sale: r.data_sale_status })),
  ...snapshot.unresolved.map(u => ({ domain: null, type: null, state: 'unknown', confidence: u.confidence, priority: u.review_priority,
    reasons: u.rationale_codes, support: [...u.support].sort(), retention: 'unknown', sale: 'unknown' }))]),
  excluded: [...snapshot.excluded].sort(), duplicates: sorted(snapshot.duplicate_groups.map(g => [...g].sort())) };
}
function harness() {
  let snapshot = initialSnapshot();
  const pending: Promise<void>[] = [], workers: SessionWorker[] = [], messages: File[][] = [];
  const session = new LocalSession(next => { snapshot = next; }, () => {
    const worker: SessionWorker = { onmessage: null, onerror: null, onmessageerror: null, terminate: vi.fn(), postMessage(selected) {
      messages.push(selected);
      const reply = worker.onmessage;
      pending.push(assessSelectedFiles(selected).then(result => { reply?.({ data: { result } } as MessageEvent); }));
    } };
    workers.push(worker); return worker;
  });
  return { session, workers, messages, get snapshot() { return snapshot; }, async settle() { await Promise.all(pending); } };
}
function checkLive(snapshot: SessionSnapshot) {
  const batch = snapshot.result!;
  const observations = new Set(batch.discovery.observations.map(o => o.id));
  expect(batch.discovery.sources).toHaveLength(snapshot.sources.length);
  for (const a of batch.assessments) {
    for (const id of a.support) expect(observations.has(id)).toBe(true);
    for (const r of a.rationales) for (const id of r.support) expect(a.support).toContain(id);
    expect(a.unknown_claims).toHaveLength(7);
    expect(a.unknown_claims.every(c => c.evidence_state === 'unknown' && c.confidence === 'insufficient')).toBe(true);
  }
  expect(JSON.stringify(snapshot)).not.toMatch(/SYNTHETIC_|From:|An account was requested|\.eml|@|token=/);
}
afterEach(() => vi.useRealTimers());

describe('integrated session uses unchanged engines and immutable oracles', () => {
  it.each(manifest.cases)('$id initial session preserves approved labels', async c => {
    const h = harness(); h.session.select(files(c.sources)); await h.settle();
    expect(project(h.snapshot.result!, c.sources)).toEqual(expected(c.expected)); checkLive(h.snapshot); h.session.dispose();
  });
  const survivors = manifest.cases.flatMap(c => c.after_delete.map((d, i) => ({ ...c, deletion: d, snapshotId: `${c.id}-d${i + 1}` })));
  it.each(survivors)('$snapshotId removal recomputes the complete survivor oracle', async c => {
    const h = harness(); h.session.select(files(c.sources)); await h.settle();
    for (const id of c.deletion.delete_sources) {
      h.session.remove(c.sources.indexOf(id) + 1);
      expect(h.snapshot.result).toBeNull(); expect(h.snapshot.opened).toEqual([]);
      await h.settle();
    }
    const ids = c.sources.filter(id => !c.deletion.delete_sources.includes(id));
    // Empty survivors intentionally have no session results or worker.
    const result = h.snapshot.result ?? await assessSelectedFiles([]);
    expect(project(result, ids)).toEqual(expected(c.deletion.expected));
    expect(h.snapshot.sources.map(s => s.id)).toEqual(ids.map(id => c.sources.indexOf(id) + 1));
    if (ids.length) checkLive(h.snapshot);
    h.session.dispose();
  });
  it('promotes an identical alternative after removing the canonical copy and retires opened actions', async () => {
    const h = harness(); const [file] = files(['e01']); h.session.select([file, file]); await h.settle();
    const a = h.snapshot.result!.assessments[0];
    h.session.markOpened(a.id, 'shop-privacy-demo-v1'); expect(h.snapshot.opened).toHaveLength(1);
    h.session.markOpened(a.id, 'clinic-account-demo-v1'); expect(h.snapshot.opened).toHaveLength(1);
    expect(h.snapshot.result!.discovery.relationship_evidence.map(e => e.role)).toEqual(['primary', 'duplicate']);
    h.session.remove(1); expect(h.snapshot.result).toBeNull(); expect(h.snapshot.opened).toEqual([]); await h.settle();
    expect(h.messages.at(-1)).toEqual([file]);
    expect(h.snapshot.sources.map(s => s.label)).toEqual(['Source 2']);
    expect(h.snapshot.result!.assessments[0].confidence).toBe(a.confidence);
    expect(h.snapshot.result!.discovery.relationship_evidence.map(e => e.role)).toEqual(['primary']);
    h.session.remove(2); expect(h.snapshot.result).toBeNull(); expect(h.snapshot.sources).toEqual([]);
    expect(h.workers.every(w => vi.mocked(w.terminate).mock.calls.length === 1)).toBe(true); h.session.dispose();
  });
  it('order changes preserve semantic outcomes; removal retires contradictions and sole context', async () => {
    const paths = ['emails/receipt-shop.eml', 'emails/conflicting-cancellation.eml', 'emails/health-context-account.eml'];
    const ids = paths.map(path => manifest.sources.find(s => s.path === path)!.id);
    for (const ordered of [ids, [...ids].reverse()]) {
      const h = harness(); h.session.select(files(ordered)); await h.settle();
      const before = h.snapshot.result!.assessments;
      expect(before.some(a => a.rule_id === 'conflicting_transaction' && a.confidence === 'low')).toBe(true);
      expect(before.some(a => a.rationale_codes.includes('HEALTH_CONTEXT'))).toBe(true);
      h.session.remove(ordered.indexOf(ids[1]) + 1); await h.settle();
      expect(h.snapshot.result!.discovery.conflicts).toEqual([]);
      expect(h.snapshot.result!.assessments.some(a => a.rule_id === 'paid_receipt' && a.confidence === 'medium')).toBe(true);
      h.session.remove(ordered.indexOf(ids[2]) + 1); await h.settle();
      expect(h.snapshot.result!.assessments.some(a => a.rationale_codes.includes('HEALTH_CONTEXT'))).toBe(false);
      expect(h.snapshot.result!.assessments.every(a => a.domain !== 'fictional-clinic.test')).toBe(true);
      checkLive(h.snapshot); h.session.dispose();
    }
  });
  it.each(['emails/registration-shop.eml', 'history/duplicate-visits.json'])('%s preserves alternatives in both removal orders', async path => {
    const id = manifest.sources.find(s => s.path === path)!.id;
    for (const removed of [1, 2]) {
      const h = harness(); const [file] = files([id]); h.session.select([file, file]); await h.settle();
      h.session.remove(removed); await h.settle();
      expect(h.snapshot.result).toEqual(await assessSelectedFiles([file]));
      expect(h.snapshot.sources[0].id).toBe(removed === 1 ? 2 : 1);
      const workerCount = h.workers.length; h.session.remove(999); expect(h.workers).toHaveLength(workerCount);
      h.session.dispose();
    }
  });
});

describe('worker lifetime and safe failure', () => {
  function controlled(factoryThrows = false) {
    const workers: SessionWorker[] = []; let snapshot = initialSnapshot();
    const session = new LocalSession(s => { snapshot = s; }, () => {
      if (factoryThrows) throw new Error('SYNTHETIC_ERROR_SECRET');
      const worker: SessionWorker = { onmessage: null, onerror: null, onmessageerror: null, postMessage: vi.fn(), terminate: vi.fn() };
      workers.push(worker); return worker;
    });
    return { session, workers, get snapshot() { return snapshot; } };
  }
  it('enforces five seconds, drops sources and ignores stale replies across supersession/clear/dispose', async () => {
    vi.useFakeTimers(); const h = controlled(); const selected = files(['e01']);
    const result = await assessSelectedFiles(selected);
    h.session.select(selected); const late = h.workers[0].onmessage!;
    h.session.select(selected); late({ data: { result } } as MessageEvent); expect(h.snapshot.result).toBeNull();
    vi.advanceTimersByTime(4999); expect(h.snapshot.busy).toBe(true);
    vi.advanceTimersByTime(1); expect(h.snapshot.status).toContain('PARSER_TIMEOUT'); expect(h.snapshot.sources).toEqual([]);
    h.session.select(selected); const late2 = h.workers[2].onmessage!; h.session.clear(); late2({ data: { result } } as MessageEvent);
    expect(h.snapshot.result).toBeNull(); expect(h.snapshot.opened).toEqual([]);
    h.session.select(selected); const beforeDispose = h.snapshot; h.session.dispose(); h.session.select(selected);
    expect(h.workers).toHaveLength(4); expect(h.snapshot).toBe(beforeDispose); // No publication into an unmounted view.
    expect(h.workers.every(w => vi.mocked(w.terminate).mock.calls.length === 1)).toBe(true);
  });
  it.each(['onerror', 'onmessageerror', 'reply', 'constructor'] as const)('%s discards session without exception echo', failure => {
    const h = controlled(failure === 'constructor'); h.session.select(files(['e01']));
    if (failure === 'reply') h.workers[0].onmessage?.({ data: { code: 'SYNTHETIC_ERROR_SECRET' } } as MessageEvent);
    else if (failure === 'onerror') h.workers[0].onerror?.(new Event('error') as ErrorEvent);
    else if (failure === 'onmessageerror') h.workers[0].onmessageerror?.(new MessageEvent('messageerror'));
    expect(h.snapshot.status).toContain('PARSER_FAILED'); expect(h.snapshot.error).toBe(true);
    expect(h.snapshot.sources).toEqual([]); expect(JSON.stringify(h.snapshot)).not.toContain('SYNTHETIC_ERROR_SECRET'); h.session.dispose();
  });
  it('rejects size/count/type limits before creating a worker', () => {
    const h = controlled();
    h.session.select(Array.from({ length: 21 }, () => files(['e01'])[0])); expect(h.snapshot.status).toContain('BATCH_LIMIT');
    h.session.select([new File([new Uint8Array(1024 * 1024 + 1)], 'large.eml')]); expect(h.snapshot.status).toContain('FILE_LIMIT');
    h.session.select([new File(['x'], 'data.zip')]); expect(h.snapshot.status).toContain('UNSUPPORTED_FILE');
    expect(h.workers).toEqual([]); h.session.dispose();
  });
  it('terminates and discards sources if posting File handles fails', () => {
    let snapshot = initialSnapshot();
    const worker: SessionWorker = { onmessage: null, onerror: null, onmessageerror: null,
      postMessage() { throw new Error('SYNTHETIC_POST_SECRET'); }, terminate: vi.fn() };
    const session = new LocalSession(next => { snapshot = next; }, () => worker);
    session.select(files(['e01'])); expect(worker.terminate).toHaveBeenCalledOnce();
    expect(snapshot.sources).toEqual([]); expect(snapshot.result).toBeNull();
    expect(snapshot.status).toContain('PARSER_FAILED'); expect(JSON.stringify(snapshot)).not.toContain('SYNTHETIC_POST_SECRET');
    session.dispose();
  });
  it('reviews each literal action separately and refuses source-derived destinations or unsupported associations', async () => {
    for (const entry of ACTION_DIRECTORY) {
      const url = new URL(entry.destination);
      expect(url.protocol).toBe('https:'); expect(url.hostname).toBe(entry.domain); expect(url.hostname.endsWith('.test')).toBe(true);
      expect(url.username + url.password + url.search + url.hash + url.port).toBe('');
      expect(readFileSync(new URL('../../../../docs/PHASE5-ACTION-REVIEWS.md', import.meta.url), 'utf8')).toContain(`## ${entry.id}`);
    }
    const a = (await assessSelectedFiles(files(['e01']))).assessments[0];
    expect(actionsFor({ ...a, domain: 'https://fictional-shop.test/?redirect=evil.test' })).toEqual([]);
    expect(actionsFor({ ...a, relationship_type: 'visited' })).toEqual([]);
    expect(actionsFor({ ...a, relationship_id: null })).toEqual([]);
  });
});
