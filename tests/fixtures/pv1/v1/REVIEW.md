# Independent ground-truth review — pending

No completed independent human review is recorded. This checklist is an input
to PR review, not a fabricated reviewer attestation. Do not add real source
data or personal contact information while reviewing.

1. Read the PR scope, corpus README and source catalog. Open raw files as text.
2. Label each source/case independently before consulting the proposed snapshot.
   Use only facts visible in the raw evidence and explicit scenario context.
3. Compare relationship type, observed/inferred state, confidence, priority,
   unresolved/excluded records, event dates, duplicate groups and source support.
4. Check each deletion snapshot against the named surviving sources; independently
   decide which claims disappear or stay, without running a deletion service.
5. Record disagreements in PR comments by case/event ID, with raw literal anchor,
   proposed correction, reason, and agreed resolution. Never use algorithm output
   as the authority. Re-run validation after reviewed corrections.
6. Only after adjudication, explicitly record acceptance and a reviewed version
   decision. The current manifest intentionally remains awaiting_independent_review.

| Case group | Review questions | Independent result |
| --- | --- | --- |
| c01, c04 | Are visits kept separate from signup/payment? Is confidence claim-specific? | Pending |
| c02, c03, c21, c28 | Are account/transaction indications cautious? Does unpaid mean no confirmed payment? | Pending |
| c05, c06, c25 | Do exact copies avoid confidence inflation? Does distinct history survive? | Pending |
| c07 | Does the contradiction prevent asserting a completed payment while retaining Sensitive review? | Pending |
| c08–c10, c29 | Do spoofing, shared transport and vague wording remain Unknown/insufficient? | Pending |
| c11, c12 | Do malformed dates remain unknown? Is missing required time explicitly excluded? | Pending |
| c13, c14 | Are unsafe URLs excluded and all sentinel query/fragment/userinfo values absent from labels? | Pending |
| c15–c17 | Are HTML, scripts, embedded instructions and the inert attachment never executed/trusted? | Pending |
| c18 | Is health context separated from a diagnosis and from account confidence? | Pending |
| c19, c20 | Does quoted text avoid false signup, and do similar domains remain separate? | Pending |
| c22, c26, c27 | Do unavailable history, absent sender, and encoded subject have the intended evidence limits? | Pending |
| c23–c25 | Do all six after-delete snapshots cite only surviving sources? | Pending |

Cross-cutting checks: all retention/sale states unknown; no current account,
card retention, breach, sale, or successful external deletion asserted; corpus
is visibly fictional; all files cataloged; no actual credentials or identities;
all disagreement resolutions remain independently reproducible from evidence.
