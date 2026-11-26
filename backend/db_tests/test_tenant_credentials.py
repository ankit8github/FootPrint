"""Finite credential matrix on the recognized fictional DB, never other identities."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from experiments.tenant_db import LOGIN_ENV, credential_for, require_distinct_credentials
from experiments.tenant_db import test_engine as make_engine

pytestmark = pytest.mark.usefixtures("bootstrap")
LOGINS = tuple(LOGIN_ENV)


def test_credentials_are_distinct() -> None:
    # The helper raises a fixed message without assertion introspection of secrets.
    require_distinct_credentials()


@pytest.mark.parametrize("login", LOGINS)
def test_own_credential_connects(login: str, monkeypatch: pytest.MonkeyPatch) -> None:
    for other, variable in LOGIN_ENV.items():
        if other != login:
            monkeypatch.delenv(variable)
    engine = make_engine(login)
    try:
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT current_user")) == login
    finally:
        engine.dispose()


@pytest.mark.parametrize("login,other", [(a, b) for a in LOGINS for b in LOGINS if a != b])
def test_other_role_credential_is_rejected(login: str, other: str) -> None:
    template = make_engine(login)
    engine = create_engine(
        template.url.set(password=credential_for(other)),
        hide_parameters=True,
        poolclass=NullPool,
        connect_args={"connect_timeout": 3},
    )
    template.dispose()
    rejected = False
    try:
        with engine.connect():
            pass
    except OperationalError as error:
        # Connection refusals/timeouts do not count as password rejection. libpq
        # startup authentication errors do not expose a reliable SQLSTATE field.
        rejected = "password authentication failed" in str(error.orig)
    finally:
        engine.dispose()
    assert rejected, "Expected password authentication rejection on the fictional listener"


def test_runtime_helper_needs_only_runtime_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    for login, variable in LOGIN_ENV.items():
        if login != "fp6_runtime_login":
            monkeypatch.delenv(variable)
    engine = make_engine("fp6_runtime_login")
    try:
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT current_user")) == "fp6_runtime_login"
    finally:
        engine.dispose()


@pytest.mark.parametrize("login", LOGINS)
def test_missing_credential_has_no_shared_fallback(
    monkeypatch: pytest.MonkeyPatch, login: str
) -> None:
    monkeypatch.delenv(LOGIN_ENV[login])
    monkeypatch.setenv("FP6_TEST_PASSWORD", "unused-legacy-value")
    with pytest.raises(RuntimeError, match="Missing or invalid role-specific"):
        make_engine(login)


def test_duplicate_credentials_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LOGIN_ENV["fp6_auth_login"], os.environ[LOGIN_ENV["fp6_runtime_login"]])
    with pytest.raises(RuntimeError, match="credentials must be distinct"):
        require_distinct_credentials()


def test_unknown_login_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="Unrecognized synthetic login"):
        make_engine("not-an-experiment-login")
