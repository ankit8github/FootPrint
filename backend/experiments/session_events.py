"""Authenticated fictional events, not an Auth0 webhook or delivery guarantee."""

import time
from collections.abc import Callable

from joserfc import jwt
from joserfc.jwk import RSAKey

from experiments.oidc_protocol import ISSUER, StrictDecoder
from experiments.session_store import (
    HANDLE,
    MAX_MARKERS,
    OWNERS,
    Denied,
    SessionStore,
    random_value,
)

EVENT_ISSUER = ISSUER + "/fictional-security-events"
EVENT_AUDIENCE = "footprint-session-fixture"
HEADER = {"alg": "RS256", "kid": "session-event-1", "typ": "secevent+jwt"}


class FictionalEvents:
    def __init__(self, store: SessionStore, wall_clock: Callable[[], float] = time.time) -> None:
        self.store = store
        self.wall_clock = wall_clock
        self.key: RSAKey | None = RSAKey.generate_key(2048)
        self.public: RSAKey | None = RSAKey.import_key(self.key.as_dict(private=False))

    def sign(self, subject: str, sequence: int, kind: str = "recovery") -> str:
        """Trusted test harness only; never exposed as a browser endpoint."""
        if self.key is None:
            raise Denied(400)
        now = int(self.wall_clock())
        return jwt.encode(
            HEADER,
            {
                "iss": EVENT_ISSUER,
                "aud": EVENT_AUDIENCE,
                "identity_issuer": ISSUER,
                "sub": subject,
                "kind": kind,
                "sequence": sequence,
                "jti": random_value(),
                "iat": now,
                "nbf": now,
                "exp": now + 60,
            },
            self.key,
        )

    async def apply(self, encoded: str) -> None:
        try:
            if not isinstance(encoded, str) or len(encoded) > 4096 or self.public is None:
                raise Denied(400)
            decoded = jwt.decode(
                encoded, self.public, algorithms=["RS256"], decoder_cls=StrictDecoder
            )
            c = decoded.claims
            if decoded.header != HEADER or set(c) != {
                "iss",
                "aud",
                "identity_issuer",
                "sub",
                "kind",
                "sequence",
                "jti",
                "iat",
                "nbf",
                "exp",
            }:
                raise Denied(400)
            if (
                c["iss"] != EVENT_ISSUER
                or c["aud"] != EVENT_AUDIENCE
                or c["identity_issuer"] != ISSUER
                or c["sub"] not in OWNERS
                or c["kind"] not in {"recovery", "mfa_reset"}
                or not isinstance(c["jti"], str)
                or not HANDLE.fullmatch(c["jti"])
                or type(c["sequence"]) is not int
                or not 1 <= c["sequence"] <= MAX_MARKERS
            ):
                raise Denied(400)
            now = int(self.wall_clock())
            if (
                any(type(c[k]) is not int for k in ("iat", "nbf", "exp"))
                or c["iat"] > now
                or c["nbf"] > now
                or c["exp"] <= now
                or not 0 < c["exp"] - c["iat"] <= 60
            ):
                raise Denied(400)
            jwt.JWTClaimsRegistry(now=now, leeway=0).validate(c)
            owner, sequence = c["sub"], c["sequence"]
        except Exception:
            raise Denied(400) from None
        await self.store.event(owner, sequence)

    def clear(self) -> None:
        self.key = self.public = None
