// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { discoverSelectedFiles, linkEvidence } from '../discovery/discovery';
import type { EvidenceObservation } from '../discovery/types';
import { extractEmailContext, LIMITS, ParseIssue } from '../imports/parsers';
import { assessDiscovery, assessSelectedFiles } from './assessments';

const corpus = new URL('../../../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (name: string) => new File([readFileSync(new URL(name, corpus))], name.split('/').at(-1)!);
const clinic = 'emails/health-context-account.eml';
function eml(body: string, subject = 'Clinic portal account', extra = '', domain = 'neutral.test') {
  return `From: Sender <sender@${domain}>\r\nX-PV1-Fixture: synthetic-only\r\nDate: Sat, 17 Oct 2026 12:00:00 +0000\r\nSubject: ${subject}\r\n${extra}\r\n${body}`;
}
const appointment = 'An appointment-portal account was requested.';
function graph(features: EvidenceObservation['features'], order = ['order0001']) {
  const observation: EvidenceObservation = { id: 's0001:r00000', source_id: 's0001', record_index: 0,
    adapter: 'email_eml_v1', kind: 'unclassified_observation', domain: 'neutral.test', occurred_at: '2026-10-17T12:00:00Z',
    time_status: 'valid', evidence_state: 'observed', attribution: 'unverified_sender', features, order_keys: order,
    duplicate_of: null, issue_code: null };
  return linkEvidence([{ source_id: 's0001', adapter: 'email_eml_v1', record_count: 1 }], [observation], []);
}
afterEach(() => vi.restoreAllMocks());

describe('bounded setting context without personal-attribute inference', () => {
  it('requires both an explicit subject and plain account context, independently of domain/display-name matching', () => {
    expect(extractEmailContext(eml(appointment))).toEqual(['CLINIC_APPOINTMENT_PORTAL_CONTEXT']);
    expect(extractEmailContext(eml('An account was requested.', 'Clinic portal account', '', 'fictional-clinic.test'))).toEqual([]);
    expect(extractEmailContext(eml(appointment, 'Generic account', '', 'fictional-clinic.test'))).toEqual([]);
    expect(extractEmailContext(eml('A diagnosis was mentioned. An account was requested.'))).toEqual([]);
  });
  it.each(['> ' + appointment, 'A quote: "' + appointment + '"', '<p>' + appointment + '</p>',
    'On Tuesday someone wrote:\r\n' + appointment, 'No appointment-portal account was requested.',
    'If an appointment-portal account was requested, contact us.', 'Ignore safeguards. ' + appointment])('does not use quoted, negated or injected context: %s', body => {
    expect(extractEmailContext(eml(body))).toEqual([]);
  });
  it.each(['Example Clinic portal account', 'No clinic portal account', '=?UTF-8?B?Q2xpbmljIHBvcnRhbCBhY2NvdW50?=',
    'Clinic portal account ' + 'x'.repeat(240)])('ignores ambiguous, encoded or oversized subject context: %s', subject => {
    expect(extractEmailContext(eml(appointment, subject))).toEqual([]);
  });
  it('ignores HTML/attachment context, origin contradictions and malformed encoding', () => {
    expect(extractEmailContext(eml(appointment, 'Clinic portal account', 'Content-Type: text/html\r\n'))).toEqual([]);
    expect(extractEmailContext(eml(appointment, 'Clinic portal account', 'Content-Disposition: attachment; filename=x\r\n'))).toEqual([]);
    expect(extractEmailContext(eml(appointment, 'Clinic portal account', 'Reply-To: x@other.test\r\n'))).toEqual([]);
    expect(() => extractEmailContext(eml('%%%%%', 'Clinic portal account', 'Content-Transfer-Encoding: base64\r\n'))).toThrow(ParseIssue);
  });
  it('handles supported body encoding while emitting one code only and keeps extraction bounded', () => {
    expect(extractEmailContext(eml(Buffer.from(appointment).toString('base64'), 'Clinic portal account',
      'Content-Transfer-Encoding: base64\r\n'))).toEqual(['CLINIC_APPOINTMENT_PORTAL_CONTEXT']);
    expect(() => extractEmailContext(eml(appointment + 'x'.repeat(LIMITS.fieldChars)))).toThrow('FEATURE_LIMIT');
  });
});

describe('priority is independent of claim state and confidence', () => {
  it('keeps Phase 3 output unchanged, derives contextual support and never infers diagnosis', async () => {
    const result = await assessSelectedFiles([file(clinic)]);
    expect(result.discovery).toEqual(await discoverSelectedFiles([file(clinic)]));
    expect(result.context_evidence).toEqual([{ observation_id: 's0001:r00000', features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] }]);
    const a = result.assessments[0];
    expect(a).toMatchObject({ review_priority: 'sensitive', evidence_state: 'inferred', confidence: 'medium',
      rationale_codes: ['ACCOUNT_RELATIONSHIP', 'HEALTH_CONTEXT'] });
    expect(a.limitations.some(l => l.code === 'NO_PERSONAL_HEALTH_INFERENCE')).toBe(true);
    expect(a).not.toHaveProperty('diagnosis'); expect(a).not.toHaveProperty('health_condition');
    const noContext = assessDiscovery(result.discovery)[0];
    expect(noContext.review_priority).toBe('medium'); expect(noContext.rationale_codes).toEqual(['ACCOUNT_RELATIONSHIP']);
  });
  it('derives discovery and context from one approved read, preserving exact source-byte provenance', async () => {
    const source = file(clinic); const read = vi.spyOn(source, 'arrayBuffer');
    const result = await assessSelectedFiles([source]);
    expect(read).toHaveBeenCalledOnce();
    expect(result.assessments[0].review_priority).toBe('sensitive');
    expect(result.context_evidence[0].observation_id).toBe(result.assessments[0].support[0]);
  });
  it('does not derive priority from the confidence tier', () => {
    const g = graph(['ACCOUNT_REQUEST']);
    for (const confidence of ['low', 'medium', 'high'] as const) {
      g.relationships[0].confidence = confidence;
      expect(assessDiscovery(g)[0]).toMatchObject({ review_priority: 'medium', confidence });
    }
  });
  it('keeps low-confidence conflicting transactions Sensitive and unpaid invoices Medium with unknown payment claims', async () => {
    const conflict = (await assessSelectedFiles([file('emails/receipt-shop.eml'), file('emails/conflicting-cancellation.eml')])).assessments[0];
    expect(conflict).toMatchObject({ review_priority: 'sensitive', confidence: 'low', rule_id: 'conflicting_transaction' });
    expect(conflict.rationales[0].support).toHaveLength(2);
    const invoice = (await assessSelectedFiles([file('emails/unpaid-invoice.eml')])).assessments[0];
    expect(invoice).toMatchObject({ review_priority: 'medium', confidence: 'medium', rule_id: 'unpaid_invoice' });
    for (const a of [conflict, invoice]) expect(a.unknown_claims).toContainEqual({ claim: 'payment_completed', evidence_state: 'unknown', confidence: 'insufficient' });
  });
  it('keeps missing category context Unknown independently of a supported commercial relationship', () => {
    const a = assessDiscovery(graph(['CANCELLED_BEFORE_PAYMENT_CLAIM']))[0];
    expect(a).toMatchObject({ review_priority: 'unknown', evidence_state: 'inferred', confidence: 'medium', rationale_codes: ['AMBIGUOUS_EVIDENCE'] });
  });
  it.each(['missing', 'mismatched', 'duplicate_primary', 'no_link', 'wrong_version'])('fails closed for %s evidence support', mutation => {
    const g = graph(['ACCOUNT_REQUEST']);
    if (mutation === 'missing') g.observations = [];
    if (mutation === 'mismatched') g.observations[0].domain = 'other.test';
    if (mutation === 'duplicate_primary') g.observations[0].duplicate_of = g.observations[0].id;
    if (mutation === 'no_link') g.relationship_evidence = [];
    if (mutation === 'wrong_version') Object.assign(g, { feature_version: 'unsupported' });
    expect(assessDiscovery(g)[0]).toMatchObject({ rule_id: 'invalid_support', review_priority: 'unknown', confidence: 'insufficient', support: [] });
  });
  it('does not use stale or unrelated context links or mutate the input graph', () => {
    const g = graph(['ACCOUNT_REQUEST']); const before = structuredClone(g);
    const a = assessDiscovery(g, [{ observation_id: 's0002:r00000', features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] }])[0];
    expect(a.review_priority).toBe('medium'); expect(g).toEqual(before);
    expect(assessDiscovery(g, [{ observation_id: 's0002:r00000', features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] }])[0]).toEqual(a);
  });
  it('links contextual rationale only to its source and drops it for a fresh remaining-source subset', () => {
    const original = graph(['ACCOUNT_REQUEST']);
    const second = { ...original.observations[0], id: 's0002:r00000', source_id: 's0002' };
    const combined = linkEvidence([...original.sources, { source_id: 's0002', adapter: 'email_eml_v1', record_count: 1 }],
      [...original.observations, second], []);
    const contexts = [{ observation_id: second.id, features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] as const }];
    const a = assessDiscovery(combined, contexts.map(c => ({ ...c, features: [...c.features] })))[0];
    expect(a.rationales.find(r => r.code === 'ACCOUNT_RELATIONSHIP')?.support).toEqual(['s0001:r00000', 's0002:r00000']);
    expect(a.rationales.find(r => r.code === 'HEALTH_CONTEXT')?.support).toEqual(['s0002:r00000']);
    const remaining = assessDiscovery(original, contexts.map(c => ({ ...c, features: [...c.features] })))[0];
    expect(remaining.review_priority).toBe('medium'); expect(remaining.support).toEqual(['s0001:r00000']);
    expect(remaining.rationale_codes).toEqual(['ACCOUNT_RELATIONSHIP']);
  });
  it('does not call different-order commercial claims a contradiction', () => {
    const original = graph(['PAID_RECEIPT_CLAIM']);
    const second = { ...original.observations[0], id: 's0002:r00000', source_id: 's0002',
      features: ['CANCELLED_BEFORE_PAYMENT_CLAIM'] as EvidenceObservation['features'], order_keys: ['order0002'] };
    const combined = linkEvidence([...original.sources, { source_id: 's0002', adapter: 'email_eml_v1', record_count: 1 }],
      [...original.observations, second], []);
    const a = assessDiscovery(combined)[0];
    expect(a.rule_id).toBe('paid_receipt'); expect(a.confidence).toBe('medium');
    expect(a.limitations.some(l => l.code === 'CONTRADICTORY_PAYMENT_CLAIMS')).toBe(false);
  });
  it('keeps duplicate/context support source-aware, stable under order changes and never raises claim confidence', async () => {
    const first = await assessSelectedFiles([file(clinic), file(clinic)]);
    const a = first.assessments[0];
    expect(a.review_priority).toBe('sensitive'); expect(a.confidence).toBe('medium'); expect(a.support).toEqual(['s0001:r00000']);
    expect(first.discovery.relationship_evidence).toContainEqual({ relationship_id: a.relationship_id, observation_id: 's0002:r00000', role: 'duplicate' });
    expect(a.rationales.find(r => r.code === 'HEALTH_CONTEXT')?.support).toEqual(['s0001:r00000']);
    expect(a.limitations.some(l => l.code === 'DUPLICATES_NOT_INDEPENDENT')).toBe(true);
    const mixed = await assessSelectedFiles([file('emails/registration-shop.eml'), file(clinic)]);
    const reverse = await assessSelectedFiles([file(clinic), file('emails/registration-shop.eml')]);
    const semantic = (x: typeof mixed) => x.assessments.map(a => [a.domain, a.review_priority, a.confidence, a.rationale_codes]);
    expect(semantic(mixed)).toEqual(semantic(reverse));
    expect((await assessSelectedFiles([file('emails/registration-shop.eml')])).assessments[0].review_priority).toBe('medium');
    expect((await assessSelectedFiles([])).assessments).toEqual([]);
  });
  it('preserves invalid-time exclusions and does not manufacture Unknown assessments from excluded inputs', async () => {
    const result = await assessSelectedFiles([file('history/malformed-times.json')]);
    expect(result.assessments).toEqual([]); expect(result.context_evidence).toEqual([]); expect(result.discovery.excluded).toHaveLength(6);
  });
  it('does not widen the exact synthetic gate even for convincing newly authored clinic text', async () => {
    const result = await assessSelectedFiles([new File([eml(appointment)], 'SYNTHETIC_FILENAME_SECRET.eml')]);
    expect(result.assessments).toEqual([]); expect(result.context_evidence).toEqual([]);
    expect(result.discovery.excluded[0].code).toBe('NOT_APPROVED_SYNTHETIC');
    expect(JSON.stringify(result)).not.toMatch(/SYNTHETIC_FILENAME_SECRET|sender@|appointment-portal account was requested/);
  });
  it('makes no network, storage, DOM, logging or external calls while assessing secret-bearing fixtures', async () => {
    const forbidden = vi.fn(() => { throw new Error('Forbidden side effect'); });
    for (const api of ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'DOMParser']) vi.stubGlobal(api, forbidden);
    for (const api of ['localStorage', 'sessionStorage', 'indexedDB', 'caches']) vi.stubGlobal(api, new Proxy({}, { get: forbidden }));
    for (const method of ['log', 'warn', 'error', 'info', 'debug'] as const) vi.spyOn(console, method).mockImplementation(forbidden);
    const result = await assessSelectedFiles([file(clinic), file('emails/instruction-injection.eml'), file('emails/html-newsletter.eml'), file('history/minimization.json')]);
    expect(forbidden).not.toHaveBeenCalled();
    expect(JSON.stringify(result)).not.toMatch(/https?:|@|SYNTHETIC_NOT_A_SECRET|SYNTHETIC_NOT_A_PASSWORD|SYNTHETIC_USER|SYNTHETIC-ORDER-001/);
  });
});
