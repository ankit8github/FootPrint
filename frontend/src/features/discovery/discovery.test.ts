// @vitest-environment node
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { extractEmailFeatures, LIMITS, ParseIssue } from '../imports/parsers';
import { discoverSelectedFiles, linkEvidence } from './discovery';
import type { EvidenceObservation, EvidenceSource } from './types';

const corpus = new URL('../../../../tests/fixtures/pv1/v1/', import.meta.url);
const file = (path: string) => new File([readFileSync(new URL(path, corpus))], path.split('/').at(-1)!);
function eml(body: string, extra = '', domain = 'fictional-shop.test') {
  return `From: Fictional <sender@${domain}>\r\nX-PV1-Fixture: synthetic-only\r\nDate: Sat, 17 Oct 2026 12:00:00 +0000\r\n${extra}\r\n${body}`;
}
function extract(body: string, extra = '') {
  return extractEmailFeatures(eml(body, extra), () => 'order0001');
}
function observation(id: string, text: string): EvidenceObservation {
  const e = extractEmailFeatures(text, (domain, reference) => domain + '/' + reference);
  return { id, source_id: id, record_index: 0, adapter: 'email_eml_v1', kind: 'unclassified_observation',
    domain: e.domain, occurred_at: e.occurred_at, time_status: e.time_status,
    evidence_state: 'observed', attribution: 'unverified_sender', features: e.features, order_keys: e.order_keys,
    duplicate_of: null, issue_code: null };
}
const sources = (rows: EvidenceObservation[]): EvidenceSource[] => rows.map(o => ({ source_id: o.source_id, adapter: o.adapter, record_count: 1 }));
afterEach(() => vi.restoreAllMocks());

describe('bounded feature extraction, never a sender-domain classifier', () => {
  it.each(['Welcome to our service.', 'You visited us.', 'Order ABC was not paid.', 'No account was requested.',
    'If an account was requested, contact us.', '> An account was requested.', 'A quote: "An account was requested."',
    '<p>An account was requested.</p>', 'https://other.test/An-account-was-requested'])('does not infer a relationship from %s', body => {
    expect(extract(body).features).toEqual([]);
  });
  it('requires explicit content despite a claimed authentication pass or a convincing display name', () => {
    const e = extract('Hello.', 'Authentication-Results: attacker; spf=pass dkim=pass dmarc=pass\r\n');
    expect(e.domain).toBe('fictional-shop.test'); expect(e.features).toEqual([]);
    expect(e.record.observation?.origin).toBe('unverified_sender');
  });
  it.each(['Reply-To: attacker@other.test\r\n', 'Return-Path: <attacker@other.test>\r\n',
    'Authentication-Results: forged; dmarc=fail\r\n'])('suppresses features for ambiguous/spoofed origins: %s', headers => {
    const e = extract('An account was requested.', headers);
    expect(e.record.code).toBe('ORIGIN_CONFLICT'); expect(e.domain).toBeNull(); expect(e.features).toEqual([]);
  });
  it('ignores HTML and attachment payloads; a plain subject cue is only weak marketing evidence', () => {
    const e = extract('<script>fetch("https://evil.test")</script>An account was requested.',
      'Subject: Fictional newsletter\r\nContent-Type: text/html\r\n');
    expect(e.features).toEqual(['NEWSLETTER_CUE']);
    expect(extract('An account was requested.', 'Content-Type: text/plain\r\nContent-Disposition: attachment; filename=x\r\n').features).toEqual([]);
    expect(extract('newsletter account', 'Subject: =?UTF-8?B?bmV3c2xldHRlcg==?=\r\n').features).toEqual([]);
  });
  it('extracts supported encodings without emitting the decoded body', () => {
    const e = extract(Buffer.from('An account was requested.').toString('base64'),
      'Content-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n');
    expect(e.features).toEqual(['ACCOUNT_REQUEST']);
    expect(JSON.stringify(e)).not.toContain('An account was requested');
    expect(extract('An account was requested=2E', 'Content-Transfer-Encoding: quoted-printable\r\n').features).toEqual(['ACCOUNT_REQUEST']);
  });
  it('flags explicit quoted context and injection as data, never instructions', async () => {
    const graph = await discoverSelectedFiles([file('emails/instruction-injection.eml'), file('emails/quoted-registration.eml')]);
    expect(graph.relationships).toEqual([]);
    expect(graph.unresolved.map(x => x.code)).toEqual(['UNTRUSTED_INSTRUCTIONS', 'QUOTED_CONTEXT']);
    expect(extract('On Tuesday someone wrote:\r\nAn account was requested.').features).toContain('QUOTED_CONTEXT');
  });
  it('keeps multiple commercial references distinct for the unresolved multi-reference guard', () => {
    const e = extractEmailFeatures(eml('Order ABC was paid. DEF was cancelled before payment.'), (_domain, reference) => reference === 'ABC' ? 'order0001' : 'order0002');
    expect(e.order_keys).toEqual(['order0001', 'order0002']);
    expect(e.features).toEqual(['CANCELLED_BEFORE_PAYMENT_CLAIM', 'PAID_RECEIPT_CLAIM']);
  });
  it('bounds aggregate plain feature text, rejects malformed MIME and never accepts an exception as a feature', () => {
    expect(() => extract('x'.repeat(LIMITS.fieldChars + 1))).toThrow('FEATURE_LIMIT');
    expect(() => extract('%%%bad-base64', 'Content-Transfer-Encoding: base64\r\n')).toThrow(ParseIssue);
    expect(() => extractEmailFeatures(eml('hello').replace(/\r\n/g, '\n'), () => 'unused')).toThrow(ParseIssue);
  });
});

describe('discovery provenance, conflict and deduplication boundaries', () => {
  it('preserves contradictory payment claims with both sources and does not assert payment or credentials', async () => {
    const graph = await discoverSelectedFiles([file('emails/receipt-shop.eml'), file('emails/conflicting-cancellation.eml')]);
    expect(graph.conflicts).toHaveLength(1);
    const r = graph.relationships[0];
    expect(r.confidence).toBe('low'); expect(r.support).toHaveLength(2);
    expect(graph.conflicts[0].support).toEqual(r.support);
    expect(r.unknown_claims).toContainEqual({ claim: 'payment_completed', evidence_state: 'unknown', confidence: 'insufficient' });
    expect(r.unknown_claims).toContainEqual({ claim: 'payment_credentials_retained', evidence_state: 'unknown', confidence: 'insufficient' });
    const reverse = await discoverSelectedFiles([file('emails/conflicting-cancellation.eml'), file('emails/receipt-shop.eml')]);
    expect(reverse.relationships.map(x => [x.domain, x.confidence, x.relationship_type])).toEqual([[r.domain, 'low', 'transaction']]);
  });
  it('does not conflict different references or domains, and never deduplicates minimized features or Message-ID alone', () => {
    const rows = [observation('a', eml('Order ABC was paid.', 'Message-ID: <same@fictional-shop.test>\r\n')),
      observation('b', eml('DEF was cancelled before payment.', 'Message-ID: <same@fictional-shop.test>\r\n')),
      observation('c', eml('ABC was cancelled before payment.', '', 'other.test'))];
    const graph = linkEvidence(sources(rows), rows, []);
    expect(graph.conflicts).toEqual([]); expect(graph.duplicate_groups).toEqual([]);
    expect(graph.relationships).toHaveLength(2); expect(graph.relationships[0].support).toHaveLength(2);
    expect(graph.relationships.every(r => r.confidence === 'medium')).toBe(true);
  });
  it('deduplicates exact selected copies while keeping distinct source provenance and no confidence increase', async () => {
    const graph = await discoverSelectedFiles([file('emails/registration-shop.eml'), file('emails/registration-shop.eml'),
      file('history/duplicate-visits.json'), file('history/duplicate-visits.json')]);
    expect(graph.sources).toHaveLength(4);
    expect(graph.duplicate_groups[0]).toEqual(['s0001:r00000', 's0002:r00000']);
    expect(graph.relationships.find(r => r.relationship_type === 'likely_account')?.confidence).toBe('medium');
    expect(graph.relationship_evidence.filter(e => e.role === 'duplicate').length).toBeGreaterThan(1);
    expect(new Set(graph.observations.map(o => o.id)).size).toBe(graph.observations.length);
    for (const group of graph.duplicate_groups) for (const id of group.slice(1)) {
      expect(graph.observations.find(o => o.id === id)?.duplicate_of).toBe(group[0]);
    }
  });
  it('does not merge distinct paths after domain/time minimization or promote a visit to account/payment evidence', async () => {
    const graph = await discoverSelectedFiles([file('history/minimization.json')]);
    expect(graph.relationships.every(r => r.relationship_type === 'visited' && r.evidence_state === 'observed')).toBe(true);
    expect(graph.observations.length).toBeGreaterThan(1); expect(graph.duplicate_groups).toEqual([]);
  });
  it('does not collapse similar account features across domains or raise confidence for repeated claims', async () => {
    const graph = await discoverSelectedFiles([file('emails/registration-shop.eml'), file('emails/registration-invalid-date.eml')]);
    expect(graph.duplicate_groups).toEqual([]);
    expect(graph.relationships).toHaveLength(2);
    expect(graph.relationships.every(r => r.confidence === 'medium' && r.support.length === 1)).toBe(true);
    expect(graph.observations[1]).toMatchObject({ occurred_at: null, time_status: 'invalid' });
    const repeated = [observation('a', eml('An account was requested.')), observation('b', eml('An account was requested. More context.'))];
    const linked = linkEvidence(sources(repeated), repeated, []);
    expect(linked.relationships[0].support).toHaveLength(2);
    expect(linked.relationships[0].confidence).toBe('medium');
    expect(linked.duplicate_groups).toEqual([]);
  });
  it('keeps an unpaid invoice a commercial interaction with unknown payment completion', async () => {
    const graph = await discoverSelectedFiles([file('emails/unpaid-invoice.eml')]);
    expect(graph.relationships[0]).toMatchObject({ relationship_type: 'transaction', confidence: 'medium', evidence_state: 'inferred' });
    expect(graph.relationships[0].limitations).toContain('UNPAID_INVOICE');
  });
  it('keeps all six invalid Chrome times excluded and unsafe URLs without inferred domains', async () => {
    const graph = await discoverSelectedFiles([file('history/malformed-times.json'), file('history/unsafe-urls.json')]);
    expect(graph.relationships).toEqual([]); expect(graph.observations).toEqual([]);
    expect(graph.excluded.filter(e => e.code === 'INVALID_TIMESTAMP')).toHaveLength(6);
    expect(graph.excluded).toHaveLength(16);
  });
  it('rejects modified bytes, wrong adapters and markers without relying on filenames or claimed synthetic flags', async () => {
    const bytes = readFileSync(new URL('emails/registration-shop.eml', corpus));
    const graph = await discoverSelectedFiles([new File([bytes, 'changed'], 'SYNTHETIC_FILENAME_SECRET.eml'), new File([bytes], 'wrong.json')]);
    expect(graph.relationships).toEqual([]);
    expect(graph.excluded.map(x => x.code)).toEqual(['NOT_APPROVED_SYNTHETIC', 'NOT_APPROVED_SYNTHETIC']);
    expect(JSON.stringify(graph)).not.toMatch(/SYNTHETIC_FILENAME_SECRET|An account was requested|sha256|digest|@/);
  });
  it('uses no network, persistent storage, logs or HTML APIs when linking secret-bearing fixtures', async () => {
    const forbidden = vi.fn(() => { throw new Error('Forbidden side effect'); });
    for (const api of ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'DOMParser']) vi.stubGlobal(api, forbidden);
    for (const api of ['localStorage', 'sessionStorage', 'indexedDB', 'caches']) vi.stubGlobal(api, new Proxy({}, { get: forbidden }));
    for (const method of ['log', 'warn', 'error', 'info', 'debug'] as const) vi.spyOn(console, method).mockImplementation(forbidden);
    const paths = ['emails/instruction-injection.eml', 'emails/html-newsletter.eml', 'emails/registration-inert-attachment.eml', 'history/minimization.json'];
    await discoverSelectedFiles(paths.map(file));
    expect(forbidden).not.toHaveBeenCalled();
  });
});
