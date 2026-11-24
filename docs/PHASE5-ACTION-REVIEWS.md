# Synthetic action directory review records

Date: 2026-11-24 (Asia/Calcutta). Independently reviewable source records for
literal fictional destinations. Review performed during AI-assisted implementation;
product-owner/architecture review pending. No independent human, live-link or
real-world ownership verification is claimed. No DNS/HTTP/redirect check occurred.

## shop-privacy-demo-v1

- Exact destination: `https://fictional-shop.test/privacy`.
- Basis: source review of the literal entry in `frontend/src/features/actions/directory.ts`.
  HTTPS, exact reserved `.test` host, fixed path, no credentials, port, query,
  fragment or redirect parameter. Synthetic design allowlist only.
- Association: exact `fictional-shop.test` plus supported likely-account or
  commercial-interaction relationship. Visits/marketing/unresolved have no action.
- Purpose: demonstrate fictional privacy instructions. No live endpoint, actual
  business, deletion mechanism or successful action is asserted.
- Review date: 2026-11-24. Revisit whenever this entry or association changes.

## clinic-account-demo-v1

- Exact destination: `https://fictional-clinic.test/account/privacy`.
- Basis: separate source review of this literal entry; HTTPS, exact reserved
  `.test` host, fixed path, no credentials/port/query/fragment/redirect parameter.
  Synthetic design allowlist only; not a healthcare-provider ownership assertion.
- Association: exact `fictional-clinic.test` and supported likely-account type.
- Purpose: fictional account instructions, without medical claims or automatic
  actions. Domain is never used to infer health context or change assessment.
- Review date: 2026-11-24. Revisit whenever this entry or association changes.

## Shared boundary

Runtime imports literal entries, never source URLs or inferred organization names.
Nothing auto-opens. User-click links use `noopener noreferrer`. `opened` records
the opening request, not browser delivery, successful deletion, verified response
or external change. `.test` normally does not resolve; browser tests intercept the
exact literal destination locally to inspect opening without external contact.
Other findings display **No verified direct link available**. No real-world
verified links are provided. Opened state resets on every recomputation, even if
the relationship survives, to avoid associating old IDs/state with new evidence.
