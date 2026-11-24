# Phase 6B-01 report — fictional OIDC protocol spike

Date: 2026-11-24 (Asia/Calcutta). Branch: `phase6b/oidc-protocol-spike`.
Base main: `167da1d9da59acbb5cfb67cb67a5a2ea78cfefbb`, synchronized and clean at
pre-flight; contains Phase 6A merge `756989a1ddc1e6fa108b320bddd16361e3c4a6d9`.
Status: implementation, local checks and fresh GitHub CI complete; delivered in
[PR #7](https://github.com/ankit8github/FootPrint/pull/7), open and unmerged.
**Phase 6B-01 only; do not merge or start 6B-02/6C.**

## Scope and file inventory

The [pre-coding plan/checklist](PHASE6B01-PLAN.md) and
[identity feasibility review](PHASE6B01-IDENTITY-FEASIBILITY.md) distinguish actual
protocol evidence from unimplemented production controls. Scope is ten files:

| File | Purpose |
| --- | --- |
| [experiments/__init__.py](../backend/experiments/__init__.py) | Isolated namespace, never imported by app |
| [oidc_protocol.py](../backend/experiments/oidc_protocol.py) | Fixed protocol constants, bounded ephemeral transactions and maintained-client/JOSE validation |
| [oidc_fixture.py](../backend/experiments/oidc_fixture.py) | Default-disabled, explicitly enabled ASGI-only fictional issuer and callback fixture |
| [test_oidc_spike.py](../backend/tests/test_oidc_spike.py) | 84 positive/adversarial/lifecycle cases |
| [pyproject.toml](../backend/pyproject.toml) | Exact Authlib/joserfc dev pins; include experiments in strict mypy coverage |
| [uv.lock](../backend/uv.lock) | Five new hashed dev dependency packages; no existing version upgrades |
| [DECISIONS.md](DECISIONS.md) | Append proposed ADR-021; preserve every previous byte of ADR history |
| [PHASE6B01-PLAN.md](PHASE6B01-PLAN.md) | Plan and OIDC-01–10 checklist written before code |
| [PHASE6B01-IDENTITY-FEASIBILITY.md](PHASE6B01-IDENTITY-FEASIBILITY.md) | Dated primary-source provider/client review, conditional costs/regions/recovery/logout and alternatives |
| PHASE6B01-REPORT.md | Executed evidence, inventory, limits and delivery |

The normal FastAPI app, API/generated schemas, frontend, prior tests, CI workflow,
migrations, draft personal-data SQL, corpus and all Phase 1–6A documents are
unchanged, except the append-only DECISIONS addition. No `.env` or credentials are
read by the spike; fixed fixture origins are independent of environment variables.

## Implemented boundaries

`create_fixture()` exposes no routes or signing key by default. Only explicit
`enabled=True` in tests constructs the two ASGI apps. There is no module-level
app, serving CLI, normal-app import/mount, login UI or environment switch. Even
activated requests require the fixed HTTPS loopback origin and loopback ASGI
client address. The fixture transport selects only two literal origins and finite
paths, uses ASGI directly and has no DNS/socket fallback, discovery or redirects.

The modeled flow is start → pinned authorization endpoint → exact callback →
code+PKCE exchange → pinned JWKS validation → fixed 303 completion/rejection.
Authlib constructs S256 and exchanges the code; joserfc imports/verifies the JWK,
signature and claims. Public test-client authentication is `none` plus PKCE; a
future confidential BFF client needs separate authentication/key-custody review.
No custom password or signature cryptography exists. Mock
keys are generated at runtime by joserfc and never saved. Only `openid` is requested.
The unsolicited fictional equal-email claim is ignored; internal identity contains
only exact issuer+subject, and callback handling discards even that result.

State/nonce/binding use separate 32-byte CSPRNG values; PKCE verifier uses 48 bytes.
Transactions and mock codes are bounded to 32 each, expire at the server's
five-minute monotonic deadline and have expiry timers, access-time pruning and
explicit shutdown cleanup. Lookup/consumption occurs synchronously before any
await, so concurrent callbacks cannot both win. Invalid attempts consume the
matching binding; there is no retry/fallback. Deadline is checked again after
exchange. Provider work also has a two-second async timeout. Fixed-size RSA/JSON
work is synchronous; the timeout is not a general CPU isolation guarantee.

The one-use `__Host-fp_oidc_spike` transaction cookie is Secure, HttpOnly, SameSite=Lax,
Path=/, no Domain, five-minute Max-Age, and deleted after success or failure.
It never confers authenticated access. Authlib clients are closed and their token
dictionary cleared in `finally`; raw provider responses/decoded claims are not
stored in application state. No account, reusable session, database row, file,
cache, browser local/session storage or saved-footprint endpoint is created.

Callback code/state necessarily exist transiently in the modeled front-channel
URL and exchange request. After handling, query bytes are cleared from ASGI scope,
the test transport strips query strings before HTTPX logs/retains handled URLs,
and the callback returns an empty fixed-path 303 with no-store/no-referrer headers.
This is fixture-specific logging protection, not a filter applied to unrelated
application logs. It does not prove that a real browser, reverse proxy, crash dump,
swap or debugger cannot retain transient bytes; no secure erasure is claimed.
The fixture must not be served through Uvicorn/proxies: production access logging,
TLS, history handling and login CSRF require separate 6B-02 review. No new actual
browser OIDC flow or TLS-handshake test is claimed; this spike uses ASGI and HTTPS
origin/cookie semantics only. Existing browser regressions still execute separately.

## Security acceptance evidence

All following entries are executed tests in the new test module, rather than
future acceptance prose. Full parametrization contributes 84 tests.

| Plan ID | Executed test evidence |
| --- | --- |
| OIDC-01 | `test_positive_exchange_and_clean_completion`, equal-email exchange and strict request field sets in the egress test |
| OIDC-02 | `test_transaction_deadline_boundary` (299/300/301), `test_deadline_rechecked_after_exchange`, binding/concurrent-callback/replay, randomness/capacity/timer/shutdown and lifespan tests |
| OIDC-03 | `test_invalid_signed_tokens_fail_closed` (23 cases), `test_alg_none_and_unsigned_token_rejected`, duplicate signed-claim rejection; malicious token constructors must actually emit the test token before rejection counts |
| OIDC-04 | `test_code_exchange_rejects_bad_binding` (PKCE, code reuse, callback and client mismatch), altered/random code callback |
| OIDC-05 | `test_authorize_rejects_unregistered_parameters`, `test_callback_manipulation_consumes_transaction`, `test_encoded_callback_alias_is_not_registered`, `test_transport_has_no_dynamic_network_target`, JOSE header URL rejection |
| OIDC-06 | `test_provider_failures_fail_closed` (token/JWKS timeout, unavailable, redirect, malformed, duplicate JSON, oversized), `test_jwks_validation` (nine key-set/key-policy cases) |
| OIDC-07 | `test_equal_email_never_links_distinct_subjects`: `(fixed issuer, fictional-a)` differs from `(fixed issuer, fictional-b)` despite identical email claims |
| OIDC-08 | `test_no_network_no_logs_no_footprint_or_session`, `test_sensitive_provider_errors_never_leak`, `test_ephemeral_clients_tokens_and_timer_cleanup`, clean callback URLs/cookies and lifecycle tests |
| OIDC-09 | `test_default_disabled_and_normal_app_unchanged` (including an ineffective enable-env variable), nonloopback rejection, socket/DNS guards during the positive protocol exchange |
| OIDC-10 | Normal-app route/schema assertions; unchanged original test files; original corpus/contract/frontend/browser regression commands below |

Leak checks capture DEBUG logging and test exact generated code, state, binding,
nonce, verifier, ID/access tokens and fictional email/body/error sentinels. The
successful flow performs no DNS or socket connect (monkeypatched to fail), and a
guard rejects Python file opens in write mode during exchange. The mock records
only bounded approved field-name/path sets after validation, never raw values;
no footprint field is admitted at start or forwarded. These checks cover this
in-process implementation, not production OS-level monitoring or unknown native
file APIs. No JavaScript/storage API is introduced; only the transient binding
cookie exists and is removed after handling.

## Executed local validation

Windows Python 3.11.9, Node 22.15.0, npm 10.9.2 and uv 0.9.29. Commands use existing
authorized execution with command-scoped Git ownership exception; no global Git
settings change. Logs/independent exit codes are in ignored
`.local/phase6b01-validation/{backend,frontend}.json`.

Dependency installation actually executed from root:
`uv add --project backend --dev 'authlib==1.9.10' 'joserfc==1.8.0'`, with
`UV_CACHE_DIR=I:/FootPrint/.cache/uv`. Development iterations used Ruff autoformat,
targeted pytest and mypy; early failures revealed the UTF-8 form media type,
Authlib's `request(..., withhold_token=True)` API, TestClient's nonloopback default
and the Windows asyncio wakeup socket. These were fixed before the final checks;
no failed run is presented as passed. A missing test-helper import was also fixed,
and negative-token builders assert emission to avoid a producer exception counting
as successful validation rejection.

Full checks are invoked by `python .local/phase6b01-validation/run_checks.py backend`
and `frontend`, each command independently captured and required to exit zero:

| Directory | Exact command | Result |
| --- | --- | --- |
| backend | `uv run --frozen ruff check .` | PASS |
| backend | `uv run --frozen ruff format --check .` | PASS, 22 files |
| backend | `uv run --frozen mypy` | PASS, 22 source files |
| backend | `uv run --frozen pytest -q` | PASS, 234 tests = original 150 + 84 spike cases; full backend checks rerun after final callback-alias hardening |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | PASS |
| backend | `uv run --frozen python -m scripts.export_phase2 --check` | PASS |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS, 29 scenarios, six survivor snapshots, 27 files/48 events |
| backend | `uv run --frozen pip-audit --cache-dir I:/FootPrint/.cache/pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| frontend | `npm.cmd run contracts:check` | PASS |
| frontend | `npm.cmd run lint` | PASS |
| frontend | `npm.cmd run typecheck` | PASS |
| frontend | `npm.cmd test` | PASS, 284 tests / 11 files |
| frontend | `npm.cmd run build` | PASS, unchanged main 527.58 kB / gzip 192.99 kB; advisory retained |
| frontend | `npm.cmd audit --audit-level=low --cache I:/FootPrint/.cache/npm` | PASS, zero known vulnerabilities |
| frontend | `npm.cmd run test:smoke` | PASS, nine Chromium scenarios |
| root | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS, optional integrations disabled |

`PLAYWRIGHT_BROWSERS_PATH=I:/FootPrint/.cache/ms-playwright` for browser checks.
Docker is not installed on this Windows host (`Get-Command docker` found no
executable); no local Docker pass is claimed. Fresh GitHub CI ran the unchanged
disposable scaffold migration roundtrip successfully, as recorded below.
P5-F01 (bundle size) and P5-F02 (real action verification) stay open.

## Documentation and preservation validation

`python .local/phase6b01-validation/validate_delivery.py` checks local Markdown
links/fragments, ten-file inventory, all original files outside the three narrow
configuration/ADR changes, original lock package records, unchanged runtime
dependencies, appended ADR history and all ten acceptance IDs. Its first run
mis-decoded Git's UTF-8 output with the Windows default encoding; explicit UTF-8
fixed the ignored checker without altering ADR history. Corpus manifest SHA-256:
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
All Phase 6A diagrams are unchanged; no new UI or diagram was introduced.

## Delivery and stop

Implementation commit: `f14e347e8454b327578955475e057328bdbd4307`.
PR [#7](https://github.com/ankit8github/FootPrint/pull/7) targets main and remains
open/unmerged. Its ten-file inventory is above. Local documentation/baseline validation passed:
25 local links/fragments, 144 original files unchanged, prior ADR history preserved,
existing dependency records unchanged, and all ten acceptance rows present. No
original oracle or runtime gate changes are authorized.

| Fresh GitHub check for implementation commit | Observed result |
| --- | --- |
| [Push CI 45346765419](https://github.com/ankit8github/FootPrint/actions/runs/45346765419) | SUCCESS; every job and step succeeded |
| [PR CI 45346783636](https://github.com/ankit8github/FootPrint/actions/runs/45346783636) | SUCCESS; every job and step succeeded |
| [GitGuardian 138283253692](https://github.com/ankit8github/FootPrint/runs/138283253692) | SUCCESS; not independent security review |

Both workflows used fresh Ubuntu 22.04 checkouts and pinned Python/Node/uv with
locked dependency installation. The push job log was inspected and explicitly
reports 234 backend tests, 284 frontend tests, nine browser tests, clean audits
and `PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
Docker evidence is the preserved scaffold only, not an auth or tenant migration.
No future session/recovery/tenant/deletion test is counted as passed here.

Delivery commands actually executed from repository root:

```powershell
git -c safe.directory=I:/FootPrint commit -m "feat: add isolated fictional OIDC protocol spike and feasibility review"
git -c safe.directory=I:/FootPrint push -u origin phase6b/oidc-protocol-spike
python .local/phase6b01-validation/github_delivery.py create-pr
python .local/phase6b01-validation/github_delivery.py ci
python .local/phase6b01-validation/github_delivery.py review-state
python .local/phase6b01-validation/validate_delivery.py
```

The existing authorized Git credential helper is used in memory for GitHub REST
delivery; no credential is printed or saved in validation output. Safe CI/job/step
metadata is stored under ignored validation tooling. Public documentation,
dependency/audit tooling and GitHub CI use external services; the mock protocol
runtime itself has no external network route. No live identity provider API call
or account provisioning was performed. At verification there were no submitted
reviews or inline review comments; CI does not imply review approval.

This report-only follow-up records implementation evidence without changing code.
Its exact final head and final fresh push/PR CI links are recorded in the PR
description after verification rather than embedding a self-referential hash here.
The feature branch is synchronized and checked clean after delivery; main remains
at the pre-flight SHA. No merge is performed.

Auth0 remains conditional; current plan/region/cost, recovery and MFA-reset event
coverage are unverified for FootPrint. There is no live provider account, signup,
credentials, registration or integration. The future <=60-second invalidation
target is unmeasured and unimplemented. Named owners, legal/retention decisions
and independent review remain unresolved. This is not tenant isolation, production
authentication or security certification.

**Do not merge.** Stop for product-owner/security review after delivering PR #7.
No durable authentication sessions, personal-data persistence, tenant tables/RLS,
real-user import/processing, provider provisioning, deployment, external integration,
Phase 6B-02 or Phase 6C is introduced.
