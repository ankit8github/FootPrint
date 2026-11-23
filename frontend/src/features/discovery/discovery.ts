import {
  LIMITS, ParseIssue, browser_chrome_json_v1, checkFileBudgets, extractEmailFeatures,
  readApprovedSource, type Adapter, type EmailFeatureEvidence,
} from '../imports/parsers';
import type { DiscoveryGraph, EvidenceObservation, EvidenceSource, ExcludedRecord, IssueCode, Relationship } from './types';

const eventId = (source: string, row: number) => `${source}:r${String(row).padStart(5, '0')}`;
function emailKind(features: EvidenceObservation['features']): EvidenceObservation['kind'] {
  if (features.includes('ACCOUNT_REQUEST')) return 'registration_email_detected';
  if (features.includes('ACCOUNT_PREFERENCES_CHANGED')) return 'account_notification_detected';
  if (features.some(x => ['PAID_RECEIPT_CLAIM', 'CANCELLED_BEFORE_PAYMENT_CLAIM', 'UNPAID_INVOICE_CLAIM'].includes(x))) return 'transaction_email_detected';
  if (features.includes('NEWSLETTER_CUE')) return 'marketing_email_detected';
  return 'unclassified_observation';
}
function emailIssue(evidence: EmailFeatureEvidence): IssueCode | null {
  if (evidence.record.disposition === 'unresolved' && evidence.record.code !== 'HTML_ONLY_IGNORED') return evidence.record.code;
  if (evidence.features.includes('UNTRUSTED_INSTRUCTIONS')) return 'UNTRUSTED_INSTRUCTIONS';
  if (evidence.features.includes('QUOTED_CONTEXT')) return 'QUOTED_CONTEXT';
  if (evidence.order_keys.length > 1) return 'MULTIPLE_COMMERCIAL_REFERENCES';
  return emailKind(evidence.features) === 'unclassified_observation' ? 'NO_SUPPORTED_FEATURE' : null;
}

/** Stateless linking over minimized observations; no deletion or persistence operations. */
export function linkEvidence(sources: EvidenceSource[], observations: EvidenceObservation[], excluded: ExcludedRecord[]): DiscoveryGraph {
  const graph: DiscoveryGraph = { schema_version: 'phase3-discovery-v1', feature_version: 'email_features_v1',
    ruleset_version: 'relationship_fusion_v1', synthetic_only: true, sources, observations,
    relationships: [], relationship_evidence: [], unresolved: [], excluded, duplicate_groups: [], conflicts: [] };
  const duplicates = new Map<string, string[]>();
  const byId = new Map(observations.map(o => [o.id, o]));
  for (const o of observations) {
    if (o.duplicate_of) {
      const canonical = byId.get(o.duplicate_of);
      if (!canonical || canonical.duplicate_of || canonical.adapter !== o.adapter) throw new Error('INVALID_EVIDENCE');
      const group = duplicates.get(canonical.id) ?? [canonical.id];
      group.push(o.id); duplicates.set(canonical.id, group);
    }
    if (o.issue_code) graph.unresolved.push({ support: [o.id], evidence_state: 'unknown', confidence: 'insufficient', code: o.issue_code });
  }
  graph.duplicate_groups = [...duplicates.values()];
  const groups = new Map<string, { domain: string; type: Relationship['relationship_type']; support: EvidenceObservation[] }>();
  for (const o of observations) {
    if (o.issue_code || o.duplicate_of || !o.domain) continue;
    const types: Relationship['relationship_type'][] = [];
    if (o.features.includes('VISIT_RECORDED')) types.push('visited');
    if (o.features.includes('ACCOUNT_REQUEST') || o.features.includes('ACCOUNT_PREFERENCES_CHANGED')) types.push('likely_account');
    if (o.features.some(x => ['PAID_RECEIPT_CLAIM', 'CANCELLED_BEFORE_PAYMENT_CLAIM', 'UNPAID_INVOICE_CLAIM'].includes(x))) types.push('transaction');
    if (o.features.includes('NEWSLETTER_CUE')) types.push('marketing');
    for (const type of types) {
      const key = `${o.domain}/${type}`;
      const group = groups.get(key) ?? { domain: o.domain, type, support: [] };
      group.support.push(o); groups.set(key, group);
    }
  }
  for (const key of [...groups.keys()].sort()) {
    const { domain, type, support } = groups.get(key)!;
    const conflicts: DiscoveryGraph['conflicts'] = [];
    if (type === 'transaction') {
      for (const order of [...new Set(support.flatMap(o => o.order_keys))].sort()) {
        const sameOrder = support.filter(o => o.order_keys.includes(order));
        if (sameOrder.some(o => o.features.includes('PAID_RECEIPT_CLAIM')) &&
          sameOrder.some(o => o.features.includes('CANCELLED_BEFORE_PAYMENT_CLAIM'))) {
          conflicts.push({ domain, order_key: order, code: 'CONTRADICTORY_PAYMENT_CLAIMS', support: sameOrder.map(o => o.id) });
        }
      }
    }
    graph.conflicts.push(...conflicts);
    const limitations: Relationship['limitations'] = ['SOURCE_RECORD_NOT_REAL_WORLD_PROOF', 'RETENTION_AND_SALE_UNKNOWN'];
    if (type !== 'visited') limitations.push('UNVERIFIED_SENDER');
    if (type === 'likely_account') limitations.push('CURRENT_ACCOUNT_UNKNOWN');
    if (type === 'transaction') {
      limitations.push('COMMERCIAL_INTERACTION_ONLY', 'PAYMENT_OUTCOME_UNKNOWN', 'PAYMENT_CREDENTIALS_UNKNOWN');
      if (support.some(o => o.features.includes('UNPAID_INVOICE_CLAIM'))) limitations.push('UNPAID_INVOICE');
      if (conflicts.length) limitations.push('CONTRADICTORY_PAYMENT_CLAIMS');
    }
    const unknown: Relationship['unknown_claims'][number]['claim'][] = ['company_retention', 'data_sale'];
    if (type !== 'visited') unknown.push('sender_authenticity');
    if (type === 'likely_account') unknown.push('current_account');
    if (type === 'transaction') unknown.push('payment_completed', 'payment_credentials_retained');
    const relationship: Relationship = { id: `rel${String(graph.relationships.length + 1).padStart(4, '0')}`,
      domain, relationship_type: type, evidence_state: type === 'visited' ? 'observed' : 'inferred',
      confidence: type === 'visited' ? 'high' : type === 'marketing' || conflicts.length ? 'low' : 'medium',
      attribution: type === 'visited' ? 'browser_record_domain' : 'unverified_sender_domain',
      support: support.map(o => o.id), retention_status: 'unknown', data_sale_status: 'unknown',
      unknown_claims: unknown.map(claim => ({ claim, evidence_state: 'unknown', confidence: 'insufficient' })), limitations };
    graph.relationships.push(relationship);
    for (const o of support) {
      graph.relationship_evidence.push({ relationship_id: relationship.id, observation_id: o.id, role: 'primary' });
      for (const copy of duplicates.get(o.id)?.slice(1) ?? []) {
        graph.relationship_evidence.push({ relationship_id: relationship.id, observation_id: copy, role: 'duplicate' });
      }
    }
  }
  return graph;
}

/** Only this hash-gated entry point is used by the browser worker. */
export async function discoverSelectedFiles(files: readonly File[]): Promise<DiscoveryGraph> {
  if (files.length === 0) return linkEvidence([], [], []); // Read-only empty survivor oracle.
  checkFileBudgets(files);
  const sources: EvidenceSource[] = [], observations: EvidenceObservation[] = [], excluded: ExcludedRecord[] = [];
  const exactCopies = new Map<string, string>(); // Approved synthetic raw digests never leave this call.
  const orders = new Map<string, string>(); // Raw references are transient, never emitted or stored.
  let count = 0;
  for (const [index, file] of files.entries()) {
    const source_id = `s${String(index + 1).padStart(4, '0')}`;
    const adapter: Adapter = file.name.toLowerCase().endsWith('.eml') ? 'email_eml_v1' : 'browser_chrome_json_v1';
    let recordCount = 1;
    try {
      const { text, digest } = await readApprovedSource(file);
      if (adapter === 'email_eml_v1') {
        const evidence = extractEmailFeatures(text, (domain, reference) => {
          const key = `${domain}\n${reference}`;
          if (!orders.has(key)) orders.set(key, `order${String(orders.size + 1).padStart(4, '0')}`);
          return orders.get(key)!;
        });
        const id = eventId(source_id, 0);
        if (evidence.record.disposition === 'excluded') {
          excluded.push({ event_id: id, source_id, record_index: 0, code: evidence.record.code });
        } else {
          const issue_code = emailIssue(evidence);
          const duplicate_of = !issue_code ? exactCopies.get(digest) ?? null : null;
          if (!issue_code && !duplicate_of) exactCopies.set(digest, id);
          observations.push({ id, source_id, record_index: 0, adapter, kind: issue_code ? 'unclassified_observation' : emailKind(evidence.features),
            domain: issue_code ? null : evidence.domain, occurred_at: evidence.occurred_at,
            time_status: evidence.time_status, evidence_state: 'observed', attribution: 'unverified_sender',
            features: evidence.features, order_keys: evidence.order_keys, duplicate_of, issue_code });
        }
      } else {
        const records = browser_chrome_json_v1(text);
        recordCount = records.length;
        const inSource = new Map<number, EvidenceObservation>();
        for (const record of records) {
          const id = eventId(source_id, record.record_index);
          if (record.disposition === 'excluded' || record.disposition === 'unresolved') {
            excluded.push({ event_id: id, source_id, record_index: record.record_index, code: record.code }); continue;
          }
          const original = record.duplicate_of_index === null ? null : inSource.get(record.duplicate_of_index)!;
          const value = record.observation;
          const duplicate_of = original?.id ?? exactCopies.get(`${digest}/${record.record_index}`) ?? null;
          const canonical = duplicate_of ? observations.find(o => o.id === duplicate_of) : undefined;
          const observation: EvidenceObservation = { id, source_id, record_index: record.record_index, adapter, kind: 'site_visit_observed',
            domain: value?.domain ?? original!.domain, occurred_at: value?.occurred_at ?? original!.occurred_at,
            time_status: 'valid', evidence_state: 'observed', attribution: 'browser_record',
            features: ['VISIT_RECORDED'], order_keys: [], duplicate_of: canonical?.duplicate_of ?? duplicate_of, issue_code: null };
          observations.push(observation); inSource.set(record.record_index, observation);
          if (!duplicate_of) exactCopies.set(`${digest}/${record.record_index}`, id);
        }
      }
    } catch (error) {
      const code: IssueCode = error instanceof ParseIssue ? error.code : error instanceof Error && error.message === 'FEATURE_LIMIT' ? 'FEATURE_LIMIT' : 'PARSER_FAILED';
      excluded.push({ event_id: eventId(source_id, 0), source_id, record_index: 0, code });
    }
    count += recordCount;
    if (count > LIMITS.records) throw new ParseIssue('RECORD_LIMIT');
    sources.push({ source_id, adapter, record_count: recordCount });
  }
  return linkEvidence(sources, observations, excluded);
}
