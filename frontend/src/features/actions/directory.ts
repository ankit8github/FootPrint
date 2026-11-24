import type { Assessment } from '../assessments/types';

/** Literal synthetic destinations only. Each entry has its own review record. */
export const ACTION_DIRECTORY = [
  { id: 'shop-privacy-demo-v1', domain: 'fictional-shop.test', types: ['likely_account', 'transaction'],
    label: 'Open synthetic shop privacy instructions', destination: 'https://fictional-shop.test/privacy',
    reviewed_at: '2026-11-24', verification_basis: 'docs/PHASE5-ACTION-REVIEWS.md#shop-privacy-demo-v1' },
  { id: 'clinic-account-demo-v1', domain: 'fictional-clinic.test', types: ['likely_account'],
    label: 'Open synthetic clinic account instructions', destination: 'https://fictional-clinic.test/account/privacy',
    reviewed_at: '2026-11-24', verification_basis: 'docs/PHASE5-ACTION-REVIEWS.md#clinic-account-demo-v1' },
] as const;

export function actionsFor(assessment: Assessment) {
  if (!assessment.relationship_id || !assessment.relationship_type) return [];
  return ACTION_DIRECTORY.filter(entry => entry.domain === assessment.domain &&
    (entry.types as readonly string[]).includes(assessment.relationship_type!));
}
