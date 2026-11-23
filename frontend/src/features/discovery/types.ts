import type { Adapter, Code, EmailFeature, Observation as ImportObservation } from '../imports/parsers';

export type Feature = EmailFeature | 'VISIT_RECORDED';
export type IssueCode = Code | 'NO_SUPPORTED_FEATURE' | 'QUOTED_CONTEXT' | 'UNTRUSTED_INSTRUCTIONS'
  | 'MULTIPLE_COMMERCIAL_REFERENCES' | 'FEATURE_LIMIT';
export interface EvidenceObservation {
  id: string;
  source_id: string;
  record_index: number;
  adapter: Adapter;
  kind: 'site_visit_observed' | 'registration_email_detected' | 'transaction_email_detected'
    | 'marketing_email_detected' | 'account_notification_detected' | 'unclassified_observation';
  domain: string | null;
  occurred_at: string | null;
  time_status: ImportObservation['time_status'];
  evidence_state: 'observed';
  attribution: 'unverified_sender' | 'browser_record';
  features: Feature[];
  order_keys: string[];
  duplicate_of: string | null;
  issue_code: IssueCode | null;
}
export interface EvidenceSource { source_id: string; adapter: Adapter; record_count: number }
export interface Relationship {
  id: string;
  domain: string;
  relationship_type: 'visited' | 'likely_account' | 'transaction' | 'marketing';
  evidence_state: 'observed' | 'inferred';
  confidence: 'high' | 'medium' | 'low';
  attribution: 'unverified_sender_domain' | 'browser_record_domain';
  support: string[];
  retention_status: 'unknown';
  data_sale_status: 'unknown';
  unknown_claims: { claim: 'sender_authenticity' | 'current_account' | 'payment_completed' | 'payment_credentials_retained'
    | 'company_retention' | 'data_sale'; evidence_state: 'unknown'; confidence: 'insufficient' }[];
  limitations: ('SOURCE_RECORD_NOT_REAL_WORLD_PROOF' | 'UNVERIFIED_SENDER' | 'CURRENT_ACCOUNT_UNKNOWN'
    | 'COMMERCIAL_INTERACTION_ONLY' | 'PAYMENT_OUTCOME_UNKNOWN' | 'PAYMENT_CREDENTIALS_UNKNOWN'
    | 'UNPAID_INVOICE' | 'CONTRADICTORY_PAYMENT_CLAIMS' | 'RETENTION_AND_SALE_UNKNOWN')[];
}
export interface ExcludedRecord {
  event_id: string; source_id: string; record_index: number; code: IssueCode;
}
export interface DiscoveryGraph {
  schema_version: 'phase3-discovery-v1';
  feature_version: 'email_features_v1';
  ruleset_version: 'relationship_fusion_v1';
  synthetic_only: true;
  sources: EvidenceSource[];
  observations: EvidenceObservation[];
  relationships: Relationship[];
  relationship_evidence: { relationship_id: string; observation_id: string; role: 'primary' | 'duplicate' }[];
  unresolved: { support: string[]; evidence_state: 'unknown'; confidence: 'insufficient'; code: IssueCode }[];
  excluded: ExcludedRecord[];
  duplicate_groups: string[][];
  conflicts: { domain: string; order_key: string; code: 'CONTRADICTORY_PAYMENT_CLAIMS'; support: string[] }[];
}
