"""Review inventory only: proposed families do not register routes or grant access."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizationRule:
    family: str
    methods: tuple[str, ...]
    session: str
    owner: str
    csrf: str
    consent_generation: str
    lifecycle: str
    implemented: bool = True


INVENTORY = (
    AuthorizationRule(
        "/_session/preauth", ("GET",), "none", "none", "bootstrap", "none", "bounded-preauth"
    ),
    AuthorizationRule(
        "/_spike/start",
        ("POST",),
        "optional-rotation",
        "validated-callback",
        "preauth",
        "none",
        "one-use-OIDC",
    ),
    AuthorizationRule(
        "/_spike/callback",
        ("GET",),
        "validated-OIDC",
        "fixed-issuer-subject",
        "OIDC-state-exception",
        "none",
        "epoch-snapshot",
    ),
    AuthorizationRule(
        "/_spike/complete|rejected", ("GET",), "none", "none", "none", "none", "fixed-response"
    ),
    AuthorizationRule(
        "/_session/me|csrf",
        ("GET",),
        "current",
        "subject-fence",
        "none",
        "none",
        "active-epoch-expiry",
    ),
    AuthorizationRule(
        "/_session/marker",
        ("POST", "PUT", "PATCH", "DELETE"),
        "current",
        "subject-fence",
        "action-bound",
        "none",
        "active-epoch-expiry",
    ),
    AuthorizationRule(
        "/_session/logout|logout-all",
        ("POST",),
        "current",
        "subject-fence",
        "action-bound",
        "none",
        "revoke-before-response",
    ),
    AuthorizationRule(
        "/_session/step-up",
        ("POST",),
        "current",
        "same-validated-subject",
        "action-bound",
        "none",
        "rotate-preserve-deadline",
    ),
    AuthorizationRule(
        "fictional-signed-events",
        (),
        "signed-harness-only",
        "subject-fence",
        "not-HTTP",
        "none",
        "next-sequence-revoke",
    ),
    AuthorizationRule(
        "/_ownership/csrf",
        ("GET",),
        "current",
        "UUID-and-subject-fence",
        "bootstrap",
        "synthetic-lifecycle",
        "active-epoch-expiry",
    ),
    AuthorizationRule(
        "/_ownership/records",
        ("GET",),
        "current",
        "every-row-filter-count-cursor",
        "none",
        "session-filter-generation-cursor",
        "synthetic-active",
    ),
    AuthorizationRule(
        "/_ownership/records/count",
        ("GET",),
        "current",
        "every-row-filter",
        "none",
        "synthetic-lifecycle",
        "synthetic-active",
    ),
    AuthorizationRule(
        "/_ownership/records/{id}",
        ("GET",),
        "current",
        "UUID-object",
        "none",
        "synthetic-lifecycle",
        "synthetic-active",
    ),
    AuthorizationRule(
        "/_ownership/records/{id}/children",
        ("GET",),
        "current",
        "parent-and-every-child",
        "none",
        "synthetic-lifecycle",
        "synthetic-active",
    ),
    AuthorizationRule(
        "/_ownership/records/{id}/children/{child}",
        ("GET",),
        "current",
        "parent-child-and-membership",
        "none",
        "synthetic-lifecycle",
        "synthetic-active",
    ),
    AuthorizationRule(
        "/_ownership/records",
        ("POST",),
        "current-final-recheck",
        "UUID-and-subject-fence",
        "create",
        "expected-generation",
        "synthetic-active-final-recheck",
    ),
    AuthorizationRule(
        "/_ownership/records/{id}",
        ("PATCH", "DELETE"),
        "current-final-recheck",
        "object-and-links-fence",
        "update-or-delete",
        "expected-generation",
        "synthetic-active-final-recheck",
    ),
    AuthorizationRule(
        "/_ownership/records/batch",
        ("POST",),
        "current-final-recheck",
        "every-ID-atomic-fence",
        "batch",
        "expected-generation",
        "synthetic-active-final-recheck",
    ),
    AuthorizationRule(
        "future:collections-imports-sources-observations",
        ("GET", "POST", "DELETE"),
        "current",
        "every-owner-collection-and-FK",
        "every-mutation",
        "explicit-save-consent-epoch-revision",
        "active-not-expired-or-deleting",
        False,
    ),
    AuthorizationRule(
        "future:relationships-unresolved-assessments-provenance",
        ("GET",),
        "current",
        "every-join-count-filter-cursor",
        "none",
        "current-eligible-generation",
        "active-no-pending-delete",
        False,
    ),
    AuthorizationRule(
        "future:actions-opened",
        ("GET", "POST"),
        "current",
        "relationship-owner-domain-type",
        "every-mutation",
        "current-generation-directory-version",
        "active-directory-not-revoked",
        False,
    ),
    AuthorizationRule(
        "future:source-clear-withdraw-expire",
        ("DELETE", "POST"),
        "current-or-authorized-job",
        "owner-fence-idempotency",
        "browser-mutation",
        "consent-epoch-revision-fence",
        "atomic-recompute-journal",
        False,
    ),
    AuthorizationRule(
        "future:account-delete-and-receipts",
        ("DELETE", "GET"),
        "fresh-for-account-delete",
        "owner-or-minimal-receipt-scope",
        "browser-mutation",
        "revoke-all-no-footprint-via-receipt",
        "journal-ack-before-complete",
        False,
    ),
    AuthorizationRule(
        "future:jobs-restore-operator",
        (),
        "separately-authorized-role",
        "trusted-persisted-control-record",
        "not-public-route",
        "epoch-generation-reconciliation",
        "separate-audit-maintenance-no-public-bypass",
        False,
    ),
)
