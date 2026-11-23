# Synthetic test fixtures

`phase0-empty.json` is an entirely synthetic empty API response shared by backend
and frontend tests. It remains unchanged and is still the app's empty demo contract.

`pv1/v1/` is the separately authorized Phase 1 corpus: entirely fictional emails,
Chrome-compatible history and baseline 1.1.0 with status
**product-owner-approved, AI-assisted baseline**. Independent blind human review
was not performed; original review materials and proposal 1.0.0 are preserved.
Start with [the corpus README](pv1/v1/README.md) and [catalog](pv1/v1/CATALOG.md).
No product code reads these raw fixtures; there is no import pipeline or classifier.
Never put actual user exports, credentials or personal information in this directory.
