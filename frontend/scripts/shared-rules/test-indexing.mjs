// Bounded pure-function differential tests. No app entry point or catalog changes.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import * as baseline from '../../../.local/phase6c03-indexing-build/baseline/pure.mjs';
import * as indexed from '../../../.local/phase6c03-indexing-build/indexed/pure.mjs';

const records = [];
const observation = (i, features = ['PAID_RECEIPT_CLAIM'], alias = 'order0001', domain = 'fictional-shop.test') => ({
  id: `s0001:r${String(i).padStart(5, '0')}`, source_id: 's0001', record_index: i,
  adapter: 'email_eml_v1', kind: 'transaction_email_detected', domain,
  occurred_at: '2026-10-17T12:00:00.000Z', time_status: 'valid', attribution: 'unverified_sender',
  features, order_keys: alias === null ? [] : [alias], duplicate_of: null, issue_code: null, evidence_state: 'observed',
});
const sources = [{ source_id: 's0001', adapter: 'email_eml_v1', record_count: 8 }];
const graph = observations => baseline.linkEvidence(structuredClone(sources), structuredClone(observations), []);
const receipt = (name, value) => records.push({ name, sha256: createHash('sha256').update(JSON.stringify(value)).digest('hex') });
function compare(name, observations, expectedRule, contexts = []) {
  const a = baseline.linkEvidence(sources, observations, []), b = indexed.linkEvidence(sources, observations, []);
  assert.deepStrictEqual(b, a, name + ': full discovery/support/order');
  const x = baseline.assessDiscovery(a, contexts), y = indexed.assessDiscovery(b, contexts);
  assert.deepStrictEqual(y, x, name + ': full assessments');
  if (expectedRule !== null) assert.equal(x[0]?.rule_id, expectedRule, name + ': expected rule');
  for (const assessment of x) {
    assert.equal(assessment.unknown_claims.length, 7);
    assert(assessment.unknown_claims.every(c => c.evidence_state === 'unknown' && c.confidence === 'insufficient'));
  }
  receipt(name, { discovery: a, assessments: x });
}
const paid = observation(0), cancelled = observation(1, ['CANCELLED_BEFORE_PAYMENT_CLAIM']);
compare('same-alias-conflict', [paid, cancelled], 'conflicting_transaction');
compare('reverse-conflict-support-order', [cancelled, paid], 'conflicting_transaction');
compare('different-alias-no-conflict', [paid, { ...cancelled, order_keys: ['order0002'] }], 'paid_receipt');
compare('cross-domain-alias-no-conflict', [paid, { ...cancelled, domain: 'fictional-studio.test' }], 'paid_receipt');
compare('unpaid-invoice', [observation(0, ['UNPAID_INVOICE_CLAIM'])], 'unpaid_invoice');
compare('both-claims-one-row', [observation(0, ['PAID_RECEIPT_CLAIM', 'CANCELLED_BEFORE_PAYMENT_CLAIM'])], 'conflicting_transaction');
compare('duplicate-alias-array-multiplicity', [{ ...paid, order_keys: ['order0001', 'order0001'] }, cancelled], 'conflicting_transaction');
compare('invalid-alias-not-assessment-conflict', [{ ...paid, order_keys: ['bad'] }, { ...cancelled, order_keys: ['bad'] }], 'paid_receipt');
compare('five-digit-alias', [{ ...paid, order_keys: ['order10000'] }, { ...cancelled, order_keys: ['order10000'] }], 'conflicting_transaction');
compare('duplicate-copy-not-independent', [paid, { ...paid, id: cancelled.id, record_index: 1, duplicate_of: paid.id }], 'paid_receipt');
compare('reversed-duplicate-copy-order', [{ ...paid, id: cancelled.id, record_index: 1, duplicate_of: paid.id }, paid], 'paid_receipt');
compare('nonequivalent-identical-values', [paid, { ...paid, id: cancelled.id, record_index: 1 }], 'paid_receipt');
compare('empty', [], null);
compare('unresolved', [{ ...paid, domain: null, issue_code: 'UNTRUSTED_INSTRUCTIONS', features: ['UNTRUSTED_INSTRUCTIONS'], order_keys: [] }], 'unknown');
const visit = { ...paid, adapter: 'browser_chrome_json_v1', features: ['VISIT_RECORDED'], attribution: 'browser_record', kind: 'site_visit_observed', order_keys: [] };
// Matching history source is required; source mismatch and invalid time remain invalid support.
compare('invalid-history-time', [{ ...visit, time_status: 'invalid', occurred_at: null }], 'invalid_support');
const account = { ...paid, kind: 'registration_email_detected', features: ['ACCOUNT_REQUEST'], order_keys: [] };
compare('account-context', [account], 'clinic_account', [{ observation_id: paid.id, features: ['CLINIC_APPOINTMENT_PORTAL_CONTEXT'] }]);
compare('account-context-removed', [account], 'account');

const mutations = {
  'missing-observation': g => { g.observations = []; },
  'repeated-observation-id': g => { g.observations.push(structuredClone(g.observations[0])); },
  'empty-support': g => { g.relationships[0].support = []; },
  'repeated-support-id': g => { g.relationships[0].support.push(paid.id); },
  'foreign-domain-support': g => { g.observations[0].domain = 'fictional-studio.test'; },
  'duplicate-primary': g => { g.observations[0].duplicate_of = cancelled.id; },
  'issue-primary': g => { g.observations[0].issue_code = 'NO_SUPPORTED_FEATURE'; },
  'wrong-type': g => { g.relationships[0].relationship_type = 'visited'; },
  'missing-source': g => { g.sources = []; },
  'wrong-source-adapter': g => { g.sources[0].adapter = 'browser_chrome_json_v1'; },
  'missing-primary-edge': g => { g.relationship_evidence = []; },
  'foreign-relationship-edge': g => { g.relationship_evidence[0].relationship_id = 'rel0002'; },
  'foreign-observation-edge': g => { g.relationship_evidence[0].observation_id = cancelled.id; },
  'duplicate-role-primary-edge': g => { g.relationship_evidence[0].role = 'duplicate'; },
  'bad-event-id': g => { g.observations[0].id = 'bad'; g.relationships[0].support = ['bad']; },
  'bad-relationship-id': g => { g.relationships[0].id = 'bad'; },
  'wrong-schema': g => { g.schema_version = 'bad'; },
  'wrong-feature-version': g => { g.feature_version = 'bad'; },
  'wrong-fusion-version': g => { g.ruleset_version = 'bad'; },
  'not-synthetic': g => { g.synthetic_only = false; },
  'nonfictional-domain': g => { g.relationships[0].domain = 'example.com'; },
};
for (const [name, mutate] of Object.entries(mutations)) {
  const g = graph([paid]); mutate(g);
  const expected = baseline.assessDiscovery(g), actual = indexed.assessDiscovery(g);
  assert.equal(expected[0].rule_id, 'invalid_support', name);
  assert.deepStrictEqual(actual, expected, name);
  receipt(name, actual);
}
for (const [name, mutate] of Object.entries({
  'repeated-primary-edge': g => { g.relationship_evidence.push(structuredClone(g.relationship_evidence[0])); },
  'repeated-source': g => { g.sources.push(structuredClone(g.sources[0])); },
  'foreign-edge-does-not-substitute': g => { g.relationship_evidence.push({ relationship_id: 'rel0002', observation_id: paid.id, role: 'primary' }); },
})) {
  const g = graph([paid]); mutate(g);
  const expected = baseline.assessDiscovery(g);
  assert.equal(expected[0].rule_id, 'paid_receipt', name);
  assert.deepStrictEqual(indexed.assessDiscovery(g), expected, name);
  receipt(name, expected);
}
for (const [name, observations] of [
  ['missing-duplicate-primary', [{ ...paid, duplicate_of: cancelled.id }]],
  ['nested-duplicate-primary', [{ ...paid, duplicate_of: cancelled.id }, { ...cancelled, duplicate_of: paid.id }]],
  ['cross-adapter-duplicate', [paid, { ...cancelled, adapter: 'browser_chrome_json_v1', duplicate_of: paid.id }]],
]) {
  for (const rules of [baseline, indexed]) assert.throws(() => rules.linkEvidence(sources, observations, []), /^Error: INVALID_EVIDENCE$/);
  receipt(name, 'INVALID_EVIDENCE');
}
console.log(JSON.stringify({ passed: records.length, records }));
