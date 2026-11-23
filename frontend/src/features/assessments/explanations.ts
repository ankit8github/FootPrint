import type { Limitation, RationaleCode, Rule } from './types';

// Fixed reviewed vocabulary. Never interpolate source text, domain, IDs or user input.
export const EXPLANATIONS: Readonly<Record<Rule, string>> = Object.freeze({
  clinic_account: 'Account-request evidence includes clinic appointment-portal context. Sensitive review concerns that setting, not a diagnosis or personal health attribute.',
  account: 'An explicit account-request or account-notification feature supports a likely account relationship for Medium review.',
  conflicting_transaction: 'Paid-receipt and cancelled-before-payment claims refer to the same order. Sensitive review preserves both contradictory claims; neither resolves payment completion.',
  paid_receipt: 'A message contains a paid-order claim. This financial interaction warrants Sensitive review; the claim does not establish actual payment completion.',
  unpaid_invoice: 'The message describes an explicitly unpaid invoice. This commercial interaction warrants Medium review and does not establish a completed payment.',
  visit: 'Validated browser records support a visit-only relationship for Low review. A visit does not establish an account or payment.',
  marketing: 'A newsletter cue supports a marketing relationship for Low review. It does not establish data sharing or sale.',
  unknown: 'Available evidence lacks sufficient unambiguous category context. Review priority remains Unknown; it is not a default Low label.',
  invalid_support: 'Evidence support is missing or inconsistent. No defensible assessment can be made from these links; review priority remains Unknown.',
});
export const RATIONALES: Readonly<Record<RationaleCode, string>> = Object.freeze({
  ACCOUNT_RELATIONSHIP: 'Explicit account-request or account-notification evidence supports this inference.',
  HEALTH_CONTEXT: 'A bounded clinic appointment-portal context feature supports contextual review only.',
  TRANSACTION_INDICATION: 'Explicit commercial interaction features support review, not proof of completed payment.',
  VISIT_ONLY: 'Validated browser visit evidence supports this relationship only.',
  MARKETING_ONLY: 'An explicit newsletter cue supports marketing contact only.',
  AMBIGUOUS_EVIDENCE: 'Attribution, category context or source support is insufficient for a more specific priority.',
});
export const LIMITATIONS: Readonly<Record<Limitation, string>> = Object.freeze({
  SOURCE_RECORD_ONLY: 'These are observations about selected synthetic records; they do not prove real-world events.',
  UNVERIFIED_SENDER: 'The sender and claimed organization are unverified. Claimed authentication headers do not establish authenticity.',
  UNKNOWN_CLAIMS: 'Current account activity, payment completion, retained payment credentials, company retention, data sale and breach status remain unknown.',
  NO_PERSONAL_HEALTH_INFERENCE: 'No diagnosis, treatment, health condition or sensitive personal attribute is inferred.',
  CONTRADICTORY_PAYMENT_CLAIMS: 'Contradictory payment claims remain unresolved; no message is selected as the authoritative payment outcome.',
  UNPAID_INVOICE: 'An explicitly unpaid invoice is commercial interaction evidence, not proof of a successful purchase or payment.',
  UNKNOWN_EVENT_TIME: 'At least one supporting email has an invalid or missing event time. Import time is not substituted.',
  DUPLICATES_NOT_INDEPENDENT: 'Exact copies preserve alternate source provenance; they are not independent corroboration and do not raise priority or confidence.',
  INSUFFICIENT_CATEGORY_CONTEXT: 'Missing or ambiguous category context stays Unknown even when a relationship has its own evidence confidence.',
  INVALID_SUPPORT: 'Missing, stale, duplicate-primary or mismatched evidence links cannot support a more specific assessment.',
});
