"""Loopback-only developer migrations, separate from the HTTP application."""

import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.pool import NullPool

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def database_url() -> URL:
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("Set a disposable local POSTGRES_PASSWORD; see README.")
    return URL.create(
        "postgresql+psycopg",
        username="pv1_dev",
        password=password,
        host="127.0.0.1",
        port=int(os.environ.get("POSTGRES_PORT", "55432")),
        database="pv1_dev",
    )


if context.is_offline_mode():
    context.configure(dialect_name="postgresql", literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(database_url(), poolclass=NullPool).connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
