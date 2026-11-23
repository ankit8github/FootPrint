import { discoverSelectedFiles } from '../discovery/discovery';
import type { DiscoveryGraph, EvidenceObservation, Relationship } from '../discovery/types';
import { registrableDomain } from '../imports/parsers';
import { EXPLANATIONS, LIMITATIONS, RATIONALES } from './explanations';
import type { Assessment, AssessmentBatch, ContextEvidence, Limitation, Priority, RationaleCode, Rule } from './types';

const safeEventId = (id: string) => /^s\d{4}:r\d{5}$/.test(id);
const has = (o: EvidenceObservation, feature: EvidenceObservation['features'][number]) => o.features.includes(feature);
const commercial = (o: EvidenceObservation) => has(o, 'PAID_RECEIPT_CLAIM') || has(o, 'CANCELLED_BEFORE_PAYMENT_CLAIM') || has(o, 'UNPAID_INVOICE_CLAIM');
function matches(o: EvidenceObservation, type: Relationship['relationship_type']): boolean {
  if (type === 'visited') return o.adapter === 'browser_chrome_json_v1' && has(o, 'VISIT_RECORDED') && o.time_status === 'valid' && o.occurred_at !== null;
  if (o.adapter !== 'email_eml_v1') return false;
  if (type === 'likely_account') return has(o, 'ACCOUNT_REQUEST') || has(o, 'ACCOUNT_PREFERENCES_CHANGED');
  if (type === 'transaction') return commercial(o);
  return type === 'marketing' && has(o, 'NEWSLETTER_CUE');
}
function result(id: string, relationship: Relationship | null, support: string[], rule: Rule,
  priority: Priority, rationales: { code: RationaleCode; support: string[] }[], limitations: Limitation[]): Assessment {
  const claims: Assessment['unknown_claims'][number]['claim'][] = ['sender_authenticity', 'current_account',
    'payment_completed', 'payment_credentials_retained', 'company_retention', 'data_sale', 'breach_status'];
  return { id, relationship_id: relationship?.id ?? null, domain: relationship?.domain ?? null,
    relationship_type: relationship?.relationship_type ?? null, review_priority: priority,
    evidence_state: relationship?.evidence_state ?? 'unknown', confidence: relationship?.confidence ?? 'insufficient',
    rule_id: rule, support: [...support].sort(), rationale_codes: rationales.map(r => r.code),
    rationales: rationales.map(r => ({ code: r.code, support: [...r.support].sort(), explanation: RATIONALES[r.code] })),
    explanation: EXPLANATIONS[rule], limitations: [...new Set(limitations)].map(code => ({ code, explanation: LIMITATIONS[code] })),
    retention_status: 'unknown', data_sale_status: 'unknown',
    unknown_claims: claims.map(claim => ({ claim, evidence_state: 'unknown', confidence: 'insufficient' })) };
}

/** Pure internal service over minimized, worker-produced evidence. Does not mutate discovery. */
export function assessDiscovery(graph: DiscoveryGraph, contexts: readonly ContextEvidence[] = []): Assessment[] {
  const byId = new Map(graph.observations.map(o => [o.id, o]));
  const assessments: Assessment[] = [];
  for (const [index, relationship] of graph.relationships.entries()) {
    const support = [...new Set(relationship.support)];
    const observations = support.map(id => byId.get(id));
    const domainValid = relationship.domain.endsWith('.test') && registrableDomain(relationship.domain) === relationship.domain;
    const valid = graph.schema_version === 'phase3-discovery-v1' && graph.synthetic_only === true &&
      graph.feature_version === 'email_features_v1' && graph.ruleset_version === 'relationship_fusion_v1' &&
      byId.size === graph.observations.length && domainValid && /^rel\d{4,5}$/.test(relationship.id) && support.length > 0 &&
      support.length === relationship.support.length && observations.every(o => o && safeEventId(o.id) &&
        o.domain === relationship.domain && !o.duplicate_of && !o.issue_code && matches(o, relationship.relationship_type) &&
        graph.sources.some(s => s.source_id === o.source_id && s.adapter === o.adapter) &&
        graph.relationship_evidence.some(e => e.relationship_id === relationship.id && e.observation_id === o.id && e.role === 'primary'));
    if (!valid) {
      assessments.push(result(`assessment${String(index + 1).padStart(4, '0')}`, null, [], 'invalid_support', 'unknown',
        [{ code: 'AMBIGUOUS_EVIDENCE', support: [] }], ['SOURCE_RECORD_ONLY', 'UNKNOWN_CLAIMS', 'INVALID_SUPPORT']));
      continue;
    }
    const evidence = observations as EvidenceObservation[];
    let rule: Rule = 'unknown', priority: Priority = 'unknown';
    const reasons: { code: RationaleCode; support: string[] }[] = [];
    const limits: Limitation[] = ['SOURCE_RECORD_ONLY', 'UNKNOWN_CLAIMS'];
    if (relationship.relationship_type !== 'visited') limits.push('UNVERIFIED_SENDER');
    if (evidence.some(o => o.time_status !== 'valid')) limits.push('UNKNOWN_EVENT_TIME');
    if (graph.relationship_evidence.some(e => e.relationship_id === relationship.id && e.role === 'duplicate')) limits.push('DUPLICATES_NOT_INDEPENDENT');
    if (relationship.relationship_type === 'likely_account') {
      const contextualSupport = evidence.filter(o => has(o, 'ACCOUNT_REQUEST') && contexts.some(c =>
        c.observation_id === o.id && c.features.includes('CLINIC_APPOINTMENT_PORTAL_CONTEXT'))).map(o => o.id);
      rule = contextualSupport.length ? 'clinic_account' : 'account'; priority = contextualSupport.length ? 'sensitive' : 'medium';
      reasons.push({ code: 'ACCOUNT_RELATIONSHIP', support });
      if (contextualSupport.length) {
        reasons.push({ code: 'HEALTH_CONTEXT', support: contextualSupport }); limits.push('NO_PERSONAL_HEALTH_INFERENCE');
      }
    } else if (relationship.relationship_type === 'transaction') {
      const sameOrderConflict = evidence.some(paid => has(paid, 'PAID_RECEIPT_CLAIM') && evidence.some(cancelled =>
        has(cancelled, 'CANCELLED_BEFORE_PAYMENT_CLAIM') && paid.order_keys.some(key => /^order\d{4,5}$/.test(key) && cancelled.order_keys.includes(key))));
      if (sameOrderConflict) { rule = 'conflicting_transaction'; priority = 'sensitive'; limits.push('CONTRADICTORY_PAYMENT_CLAIMS'); }
      else if (evidence.some(o => has(o, 'PAID_RECEIPT_CLAIM'))) { rule = 'paid_receipt'; priority = 'sensitive'; }
      else if (evidence.every(o => has(o, 'UNPAID_INVOICE_CLAIM'))) { rule = 'unpaid_invoice'; priority = 'medium'; }
      if (rule !== 'unknown') reasons.push({ code: 'TRANSACTION_INDICATION', support });
      if (evidence.some(o => has(o, 'UNPAID_INVOICE_CLAIM'))) limits.push('UNPAID_INVOICE');
    } else if (relationship.relationship_type === 'visited') {
      rule = 'visit'; priority = 'low'; reasons.push({ code: 'VISIT_ONLY', support });
    } else if (relationship.relationship_type === 'marketing') {
      rule = 'marketing'; priority = 'low'; reasons.push({ code: 'MARKETING_ONLY', support });
    }
    if (rule === 'unknown') { reasons.push({ code: 'AMBIGUOUS_EVIDENCE', support }); limits.push('INSUFFICIENT_CATEGORY_CONTEXT'); }
    assessments.push(result(`assessment${String(index + 1).padStart(4, '0')}`, relationship, support, rule, priority, reasons, limits));
  }
  for (const unresolved of graph.unresolved) {
    const support = unresolved.support.filter(id => safeEventId(id) && byId.get(id)?.issue_code);
    assessments.push(result(`assessment${String(assessments.length + 1).padStart(4, '0')}`, null, support, 'unknown', 'unknown',
      [{ code: 'AMBIGUOUS_EVIDENCE', support }], ['SOURCE_RECORD_ONLY', 'UNVERIFIED_SENDER', 'UNKNOWN_CLAIMS', 'INSUFFICIENT_CATEGORY_CONTEXT']));
  }
  return assessments;
}

/** Sole UI entry: retains Phase 3 output byte-for-byte; context is transient and separately versioned. */
export async function assessSelectedFiles(files: readonly File[]): Promise<AssessmentBatch> {
  const context_evidence: ContextEvidence[] = [];
  const discovery = await discoverSelectedFiles(files, (observation_id, features) => {
    if (features.length) context_evidence.push({ observation_id, features });
  });
  return { schema_version: 'phase4-assessment-v1', ruleset_version: 'sensitivity_rules_v1',
    context_version: 'email_context_v1', synthetic_only: true, discovery, context_evidence,
    assessments: assessDiscovery(discovery, context_evidence) };
}
