# PV1 synthetic corpus 1.0.0 catalog

Every input is fictional and authored from scratch. Proposed labels await independent review.
No classifier output was used. See README.md for the annotation protocol and limitations.

## Sources

| ID | Raw file | Evidence / adversarial coverage |
| --- | --- | --- |
| e01 | [emails/registration-shop.eml](emails/registration-shop.eml) | registration |
| e02 | [emails/receipt-shop.eml](emails/receipt-shop.eml) | receipt |
| e03 | [emails/marketing-news.eml](emails/marketing-news.eml) | marketing |
| e04 | [emails/registration-shop-copy.eml](emails/registration-shop-copy.eml) | email_duplicate, registration |
| e05 | [emails/conflicting-cancellation.eml](emails/conflicting-cancellation.eml) | conflicting_evidence, receipt |
| e06 | [emails/account-notification.eml](emails/account-notification.eml) | account_notification |
| e07 | [emails/ambiguous-welcome.eml](emails/ambiguous-welcome.eml) | ambiguous_origin |
| e08 | [emails/phishing-display-name.eml](emails/phishing-display-name.eml) | spoofed_origin, phishing_origin |
| e09 | [emails/spoofed-from-domain.eml](emails/spoofed-from-domain.eml) | spoofed_origin |
| e10 | [emails/shared-delivery-provider.eml](emails/shared-delivery-provider.eml) | shared_delivery, ambiguous_origin |
| e11 | [emails/registration-invalid-date.eml](emails/registration-invalid-date.eml) | registration, malformed_email_timestamp |
| e12 | [emails/html-newsletter.eml](emails/html-newsletter.eml) | marketing, html_content |
| e13 | [emails/instruction-injection.eml](emails/instruction-injection.eml) | prompt_injection, ambiguous_origin |
| e14 | [emails/registration-inert-attachment.eml](emails/registration-inert-attachment.eml) | registration, attachment |
| e15 | [emails/health-context-account.eml](emails/health-context-account.eml) | registration, health_context |
| e16 | [emails/missing-from-header.eml](emails/missing-from-header.eml) | malformed_header |
| e17 | [emails/similar-name-unrelated.eml](emails/similar-name-unrelated.eml) | registration, similar_domains |
| e18 | [emails/quoted-registration.eml](emails/quoted-registration.eml) | quoted_registration, ambiguous_origin |
| e19 | [emails/unpaid-invoice.eml](emails/unpaid-invoice.eml) | unpaid_invoice, receipt |
| e20 | [emails/encoded-subject.eml](emails/encoded-subject.eml) | encoded_header, registration |
| h01 | [history/core.json](history/core.json) | visits_only |
| h02 | [history/visits-only.json](history/visits-only.json) | visits_only, old_visit |
| h03 | [history/duplicate-visits.json](history/duplicate-visits.json) | visits_only, history_duplicate |
| h04 | [history/minimization.json](history/minimization.json) | visits_only, query_fragment, url_credentials |
| h05 | [history/unsafe-urls.json](history/unsafe-urls.json) | unsafe_url |
| h06 | [history/malformed-times.json](history/malformed-times.json) | malformed_history_timestamp, missing_history_timestamp, visits_only |
| h07 | [history/encrypted-history.json](history/encrypted-history.json) | encrypted_history |

## Scenario oracle

Stable IDs locate the corresponding source cards and expected snapshots in manifest.json.

| Case | Sources | Proposed relationships | Reason |
| --- | --- | --- | --- |
| c01: Visits only, including misleading URL paths | h02 | fictional-museum.test / visited / low / high; fictional-library.test / visited / low / high | The paths /signup and /checkout are visits, not proof of an account or payment. The old event is dated explicitly and does not imply complete history. |
| c02: Registration-like message only | e01 | fictional-shop.test / likely_account / medium / medium | The literal account-request wording supports a likely account with medium evidence confidence. It does not confirm current account activity. |
| c03: Receipt only | e02 | fictional-shop.test / transaction / sensitive / medium | The explicit paid receipt indicates a past transaction and Sensitive review. No account registration or card retention follows from the receipt alone. |
| c04: Two-source shopping relationship | e01, e02, h01 | fictional-shop.test / likely_account / medium / medium; fictional-shop.test / transaction / sensitive / medium; fictional-shop.test / visited / low / high; fictional-news.test / visited / low / high | Keep account, transaction and visit claims separate. A history visit corroborates interaction without independently proving registration or payment; confidence stays medium for those claims. |
| c05: Duplicate welcome messages | e01, e04 | fictional-shop.test / likely_account / medium / medium | e04 is an exact second copy of e01. It must not create a second account or increase the claim confidence. |
| c06: Duplicate and distinct history events | h03 | fictional-duplicate.test / visited / low / high | The first two rows are identical, while the third has a different time. Deduplicate the former without losing the latter. |
| c07: Contradictory receipt and cancellation | e02, e05 | fictional-shop.test / transaction / sensitive / low | Both messages refer to the same fictional order and contradict payment status. A transaction indication remains, with low confidence; a completed payment cannot be asserted. |
| c08: Display-name phishing origin | e08 | Unknown / insufficient (unresolved) | The visible From address and destination differ from the impersonated brand. Do not associate an account with Fictional Shop or automatically visit the verification link. |
| c09: Spoofed same-domain From header | e09 | Unknown / insufficient (unresolved) | A claimed From domain is not proof of ownership. Authentication failure and contradictory Return-Path/Reply-To support Unknown and insufficient evidence. |
| c10: Shared marketing transport is not the company | e10 | Unknown / insufficient (unresolved) | A provider sender and a brand display name do not establish a reviewed organization mapping. Keep this unresolved rather than merging the provider with the garden. |
| c11: Registration with malformed email date | e11 | fictional-date.test / likely_account / medium / medium | The account-like wording supports the relationship, but the event date must remain null with an invalid-date annotation; no import-time substitution is allowed. |
| c12: History timestamps are invalid or absent | h06 | fictional-clock.test / visited / low / low | String/null/negative/overflow/fractional times are deliberately invalid. Their valid fictional domain supports only a cautious visit; timestamps stay null. Missing required field is excluded. |
| c13: Unsafe URLs are excluded | h05 | No established relationships; excluded records | These are intentional non-web, malformed, relative or local/private URL vectors. No requests or digital relationships should result. |
| c14: Query, fragment and URL credentials are minimized | h04 | fictional-shop.test / visited / low / high | Only the known fictional host and timestamp are relevant. All sentinel query, fragment, username and password-like text must be stripped in a later parser, which is not implemented here. |
| c15: Plain and HTML-only promotional messages | e03, e12 | fictional-news.test / marketing / low / low; fictional-postcard.test / marketing / low / low | Both messages explicitly describe newsletters. HTML is untrusted text: scripts must not execute and the remote image must not load. Neither establishes registration or sale. |
| c16: Prompt-like content is inert evidence | e13 | Unknown / insufficient (unresolved) | The email contains adversarial instructions and a fictional exfiltration destination. It is not an authorized instruction, and supplies no stable relationship evidence. |
| c17: Registration with an attachment that must be ignored | e14 | fictional-parcel.test / likely_account / medium / medium | Only the textual message part supports a likely account. The attachment is inert fixture text and must never be opened or used as extra evidence. |
| c18: High-impact context separate from confidence | e15 | fictional-clinic.test / likely_account / sensitive / medium | A clinic portal context warrants Sensitive review despite only medium confidence in a likely account. No diagnosis or patient facts may be inferred. |
| c19: Quoted welcome is not a registration | e18 | Unknown / insufficient (unresolved) | The outer message says that the registration sentence is an example quote. Neither the forwarder nor the quoted brand becomes a likely account. |
| c20: Similar names remain separate domains | e01, e17 | fictional-shop.test / likely_account / medium / medium; fictional-shopper.test / likely_account / medium / medium | The literal sender domains differ: fictional-shop.test and fictional-shopper.test. No alias map exists, so similar names cannot merge them. |
| c21: Invoice does not prove a completed payment | e19 | fictional-studio.test / transaction / sensitive / medium | The invoice is a financial interaction indication, but the text explicitly says unpaid. Sensitive review does not assert successful purchase or stored card details. |
| c22: Encrypted history supplies no visits | h07 | No established relationships; excluded records | The documented Chrome unavailable-history sentinel is a string rather than a visit object. Its presence cannot establish any visited domain. |
| c23: Delete sole supporting source | e01 | fictional-shop.test / likely_account / medium / medium | These are authored before/after labels, not a deletion implementation. Removing the sole source must leave no relationship or stale evidence citation. |
| c24: Delete overlapping email or history sources | e01, e02, h01 | fictional-shop.test / likely_account / medium / medium; fictional-shop.test / transaction / sensitive / medium; fictional-shop.test / visited / low / high; fictional-news.test / visited / low / high | The before/after oracles make provenance explicit: deleting email leaves only visits; deleting history keeps only email-backed claims; deleting all removes every claim. |
| c25: Delete either of two identical source copies | e01, e04 | fictional-shop.test / likely_account / medium / medium | Duplicate imports retain separate source provenance. Deleting one leaves the other with the same cautious confidence; no stale citation to the removed copy remains. |
| c26: Missing sender header | e16 | No established relationships; excluded records | No sender domain can be established from this invalid fixture. Do not invent an organization or expose a relationship despite account-like subject text. |
| c27: Encoded header registration | e20 | fictional-cafe.test / likely_account / medium / medium | The encoded subject and plain body describe a fictional account request. Phase 1 only pins raw bytes and anchors; decoding is a later adapter concern. |
| c28: Account notification is not current account proof | e06 | fictional-notes.test / likely_account / medium / medium | A settings-change notification supports a likely past account interaction with medium confidence. It does not prove current activity, current retention or sale. |
| c29: Ambiguous generic welcome | e07 | Unknown / insufficient (unresolved) | Generic welcome has no reliable account, newsletter or transaction context. |
