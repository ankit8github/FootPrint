"""Fictional server-owned identity registry and revocable principals, never app auth."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID

from experiments.oidc_protocol import ISSUER
from experiments.session_store import Denied, Session, SessionStore, Unavailable

# Assigned deterministic UUIDs only for these two fictional test identities.
IDENTITIES = MappingProxyType(
    {
        (ISSUER, "fictional-a"): UUID("a0000000-0000-4000-8000-000000000001"),
        (ISSUER, "fictional-b"): UUID("b0000000-0000-4000-8000-000000000001"),
    }
)
OPERATIONS = ("create", "update", "delete", "batch")
CSRF_BASE = "POST:/_session/marker"


@dataclass(frozen=True, repr=False)
class AuthenticatedPrincipal:
    issuer: str
    subject: str
    owner_id: UUID
    session_key: str
    auth_epoch: int


class PrincipalAuthority:
    """Only current server sessions establish authority; claims/email are not inputs."""

    def __init__(self, store: SessionStore) -> None:
        self.store = store

    def resolve(self, handle: str) -> AuthenticatedPrincipal:
        key, session = self.store.lookup(handle)
        # SessionStore.login accepts only Protocol.finish's fixed issuer/subjects.
        # Session.owner is that validated subject, not a browser supplied owner UUID.
        owner = IDENTITIES.get((ISSUER, session.owner))
        if owner is None:
            raise Denied()
        return AuthenticatedPrincipal(ISSUER, session.owner, owner, key, session.epoch)

    def validate(self, principal: AuthenticatedPrincipal) -> Session:
        if type(principal) is not AuthenticatedPrincipal:
            raise Denied()
        if (
            type(principal.issuer) is not str
            or type(principal.subject) is not str
            or type(principal.owner_id) is not UUID
            or type(principal.auth_epoch) is not int
            or type(principal.session_key) is not str
            or IDENTITIES.get((principal.issuer, principal.subject)) != principal.owner_id
        ):
            raise Denied()
        session = self.store.by_key(principal.session_key)
        if session.owner != principal.subject or session.epoch != principal.auth_epoch:
            raise Denied()
        return session

    def tokens(self, principal: AuthenticatedPrincipal) -> dict[str, str]:
        session = self.validate(principal)
        try:
            base = dict(session.tokens)[CSRF_BASE]
            return {
                operation: hmac.new(
                    base.encode("ascii"),
                    ("fictional-ownership-v1:" + operation).encode("ascii"),
                    hashlib.sha256,
                ).hexdigest()
                for operation in OPERATIONS
            }
        except Exception:
            raise Unavailable() from None

    def csrf(self, principal: AuthenticatedPrincipal, operation: str, token: str) -> None:
        expected = self.tokens(principal).get(operation)
        if (
            expected is None
            or type(token) is not str
            or len(token) != 64
            or any(character not in "0123456789abcdef" for character in token)
            or not secrets.compare_digest(expected, token)
        ):
            raise Denied(403)
