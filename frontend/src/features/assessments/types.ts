import type { DiscoveryGraph, Relationship } from '../discovery/types';
import type { ContextFeature } from '../imports/parsers';

export type Priority = 'sensitive' | 'medium' | 'low' | 'unknown';
export type RationaleCode = 'ACCOUNT_RELATIONSHIP' | 'HEALTH_CONTEXT' | 'TRANSACTION_INDICATION'
  | 'VISIT_ONLY' | 'MARKETING_ONLY' | 'AMBIGUOUS_EVIDENCE';
export type Rule = 'clinic_account' | 'account' | 'conflicting_transaction' | 'paid_receipt'
  | 'unpaid_invoice' | 'visit' | 'marketing' | 'unknown' | 'invalid_support';
export type Limitation = 'SOURCE_RECORD_ONLY' | 'UNVERIFIED_SENDER' | 'UNKNOWN_CLAIMS'
  | 'NO_PERSONAL_HEALTH_INFERENCE' | 'CONTRADICTORY_PAYMENT_CLAIMS' | 'UNPAID_INVOICE'
  | 'UNKNOWN_EVENT_TIME' | 'DUPLICATES_NOT_INDEPENDENT' | 'INSUFFICIENT_CATEGORY_CONTEXT'
  | 'INVALID_SUPPORT';
export interface ContextEvidence { observation_id: string; features: ContextFeature[] }
export interface Assessment {
  id: string;
  relationship_id: string | null;
  domain: string | null;
  relationship_type: Relationship['relationship_type'] | null;
  review_priority: Priority;
  evidence_state: 'observed' | 'inferred' | 'unknown';
  confidence: 'high' | 'medium' | 'low' | 'insufficient';
  rule_id: Rule;
  support: string[];
  rationale_codes: RationaleCode[];
  rationales: { code: RationaleCode; support: string[]; explanation: string }[];
  explanation: string;
  limitations: { code: Limitation; explanation: string }[];
  retention_status: 'unknown';
  data_sale_status: 'unknown';
  unknown_claims: { claim: 'sender_authenticity' | 'current_account' | 'payment_completed'
    | 'payment_credentials_retained' | 'company_retention' | 'data_sale' | 'breach_status';
    evidence_state: 'unknown'; confidence: 'insufficient' }[];
}
export interface AssessmentBatch {
  schema_version: 'phase4-assessment-v1';
  ruleset_version: 'sensitivity_rules_v1';
  context_version: 'email_context_v1';
  synthetic_only: true;
  discovery: DiscoveryGraph;
  context_evidence: ContextEvidence[];
  assessments: Assessment[];
}
