"""Fictional loopback-only protocol spike, not an authentication service."""

import asyncio
import json
import re
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client  # type: ignore[import-untyped]
from httpx2 import AsyncBaseTransport, Response
from joserfc import jwt
from joserfc.jwk import RSAKey

ISSUER = "https://127.0.0.1:9443"
BFF = "https://127.0.0.1:9444"
AUTHORIZE = ISSUER + "/authorize"
TOKEN = ISSUER + "/token"
JWKS = ISSUER + "/jwks"
CALLBACK = BFF + "/_spike/callback"
CLIENT_ID = "footprint-fictional-spike"
COOKIE = "__Host-fp_oidc_spike"
DEADLINE = 300
MAX_TRANSACTIONS = 32
MAX_RESPONSE = 16_384
EXCHANGE_TIMEOUT = 2
OPAQUE = re.compile(r"[A-Za-z0-9_-]{43,128}\Z")


class Rejected(Exception):
    """Never include provider input, library errors or credentials."""

    def __init__(self) -> None:
        super().__init__("OIDC_SPIKE_REJECTED")


@dataclass(frozen=True)
class Identity:
    issuer: str
    subject: str


@dataclass(repr=False)
class Transaction:
    state: str
    nonce: str
    verifier: str
    expires: float
    timer: asyncio.TimerHandle | None = field(default=None, repr=False)


def strict_json(raw: bytes) -> Any:
    """Bounded JSON with no duplicate keys or non-finite values."""
    if len(raw) > MAX_RESPONSE:
        raise Rejected()

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise Rejected()
            result[key] = value
        return result

    def invalid(value: str) -> Any:
        raise Rejected()

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


class StrictDecoder(json.JSONDecoder):
    def decode(self, s: str, _w: Any = None) -> Any:
        return strict_json(s.encode())


def public_key(raw: bytes) -> RSAKey:
    data = strict_json(raw)
    if not isinstance(data, dict) or set(data) != {"keys"}:
        raise Rejected()
    keys = data["keys"]
    if not isinstance(keys, list) or len(keys) != 1 or not isinstance(keys[0], dict):
        raise Rejected()
    key = keys[0]
    if set(key) != {"kty", "kid", "alg", "use", "key_ops", "n", "e"}:
        raise Rejected()
    if (key["kty"], key["kid"], key["alg"], key["use"], key["key_ops"]) != (
        "RSA",
        "spike-key-1",
        "RS256",
        "sig",
        ["verify"],
    ):
        raise Rejected()
    if not all(isinstance(key[k], str) for k in ("n", "e")):
        raise Rejected()
    imported = RSAKey.import_key(key)
    if imported.public_key.key_size != 2048 or imported.public_key.public_numbers().e != 65537:
        raise Rejected()
    return imported


class Protocol:
    """One process, one event loop; explicit fixture activation only."""

    def __init__(
        self,
        transport: AsyncBaseTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self.transport = transport
        self.clock = clock
        self.wall_clock = wall_clock
        self.transactions: dict[str, Transaction] = {}

    def discard(self, binding: str) -> Transaction | None:
        tx = self.transactions.pop(binding, None)
        if tx and tx.timer:
            tx.timer.cancel()
        return tx

    def clear(self) -> None:
        for binding in list(self.transactions):
            self.discard(binding)

    def _prune(self) -> None:
        for binding, tx in list(self.transactions.items()):
            if self.clock() >= tx.expires:
                self.discard(binding)

    def _client(self) -> Any:
        client = AsyncOAuth2Client(
            CLIENT_ID,
            token_endpoint_auth_method="none",
            redirect_uri=CALLBACK,
            scope="openid",
            code_challenge_method="S256",
            transport=self.transport,
            trust_env=False,
            follow_redirects=False,
            timeout=2,
        )
        client.register_compliance_hook("access_token_response", self._token_response)
        return client

    @staticmethod
    def _token_response(response: Response) -> Response:
        if (
            response.status_code != 200
            or response.headers.get("content-type") != "application/json"
        ):
            raise Rejected()
        data = strict_json(response.content)
        if not isinstance(data, dict) or set(data) != {
            "access_token",
            "token_type",
            "id_token",
            "expires_in",
        }:
            raise Rejected()
        if (
            data["token_type"] != "Bearer"
            or type(data["expires_in"]) is not int
            or not 0 < data["expires_in"] <= DEADLINE
        ):
            raise Rejected()
        if not isinstance(data["access_token"], str) or not OPAQUE.fullmatch(data["access_token"]):
            raise Rejected()
        if not isinstance(data["id_token"], str) or len(data["id_token"]) > 8192:
            raise Rejected()
        return response

    async def begin(self) -> tuple[str, str]:
        self._prune()
        if len(self.transactions) >= MAX_TRANSACTIONS:
            raise Rejected()
        binding, state, nonce = (secrets.token_urlsafe(32) for _ in range(3))
        tx = Transaction(state, nonce, secrets.token_urlsafe(48), self.clock() + DEADLINE)
        self.transactions[binding] = tx
        tx.timer = asyncio.get_running_loop().call_later(DEADLINE, self.discard, binding)
        try:
            async with asyncio.timeout(EXCHANGE_TIMEOUT), self._client() as client:
                url, _ = client.create_authorization_url(
                    AUTHORIZE, state=state, nonce=nonce, code_verifier=tx.verifier
                )
                return str(url), binding
        except Exception:
            self.discard(binding)
            raise Rejected() from None

    async def finish(self, binding: str, params: dict[str, str]) -> Identity:
        # Pop before any await: every attempt consumes its browser-bound transaction.
        tx = self.discard(binding)
        self._prune()
        if tx is None or self.clock() >= tx.expires:
            raise Rejected()
        if set(params) != {"code", "state", "iss"}:
            raise Rejected()
        if not OPAQUE.fullmatch(params["code"]) or not OPAQUE.fullmatch(params["state"]):
            raise Rejected()
        if not secrets.compare_digest(params["state"], tx.state) or params["iss"] != ISSUER:
            raise Rejected()
        try:
            async with asyncio.timeout(EXCHANGE_TIMEOUT), self._client() as client:
                try:
                    token = await client.fetch_token(
                        TOKEN,
                        grant_type="authorization_code",
                        code=params["code"],
                        code_verifier=tx.verifier,
                    )
                    if set(token) != {
                        "access_token",
                        "token_type",
                        "id_token",
                        "expires_in",
                        "expires_at",
                    }:
                        raise Rejected()
                    if token["token_type"] != "Bearer" or not isinstance(token["id_token"], str):
                        raise Rejected()
                    response = await client.request("GET", JWKS, withhold_token=True)
                    if (
                        response.status_code != 200
                        or response.headers.get("content-type") != "application/json"
                    ):
                        raise Rejected()
                    key = public_key(response.content)
                    decoded = jwt.decode(
                        token["id_token"], key, algorithms=["RS256"], decoder_cls=StrictDecoder
                    )
                    if set(decoded.header) != {"alg", "kid", "typ"} or decoded.header != {
                        "alg": "RS256",
                        "kid": "spike-key-1",
                        "typ": "JWT",
                    }:
                        raise Rejected()
                    claims = decoded.claims
                    if set(claims) - {
                        "iss",
                        "sub",
                        "aud",
                        "azp",
                        "nonce",
                        "iat",
                        "exp",
                        "nbf",
                        "email",
                    }:
                        raise Rejected()
                    for name in ("iat", "exp", "nbf"):
                        if type(claims.get(name)) is not int:
                            raise Rejected()
                    if claims["exp"] <= claims["iat"] or claims["exp"] - claims["iat"] > DEADLINE:
                        raise Rejected()
                    # Narrow single-audience profile; multi-audience tokens are rejected.
                    if claims.get("aud") != CLIENT_ID or claims.get("azp", CLIENT_ID) != CLIENT_ID:
                        raise Rejected()
                    if claims.get("iss") != ISSUER or not isinstance(claims.get("nonce"), str):
                        raise Rejected()
                    if not secrets.compare_digest(claims["nonce"], tx.nonce):
                        raise Rejected()
                    now = int(self.wall_clock())
                    if claims["exp"] <= now or claims["iat"] > now or claims["nbf"] > now:
                        raise Rejected()
                    jwt.JWTClaimsRegistry(
                        now=now,
                        leeway=0,
                        iss={"essential": True, "value": ISSUER},
                        aud={"essential": True, "value": CLIENT_ID},
                        nonce={"essential": True, "value": tx.nonce},
                        sub={"essential": True},
                        iat={"essential": True},
                        exp={"essential": True},
                        nbf={"essential": True},
                    ).validate(claims)
                    if claims["sub"] not in {"fictional-a", "fictional-b"}:
                        raise Rejected()
                    if self.clock() >= tx.expires:
                        raise Rejected()
                    return Identity(ISSUER, claims["sub"])
                finally:
                    # Authlib otherwise keeps OAuth tokens on its ephemeral client.
                    if client.token:
                        client.token.clear()
        except Exception:
            raise Rejected() from None
