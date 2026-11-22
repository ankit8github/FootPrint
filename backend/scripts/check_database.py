"""Validate only the Phase 0 migration on a disposable local database.

Refuse unexpected tables before any downgrade. No imported records are written.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

root = Path(__file__).resolve().parents[2]
load_dotenv(root / ".env")
password = os.environ.get("POSTGRES_PASSWORD")
if not password:
    raise SystemExit("Generate a local POSTGRES_PASSWORD first; see README.")
url = URL.create(
    "postgresql+psycopg",
    username="pv1_dev",
    password=password,
    host="127.0.0.1",
    port=int(os.environ.get("POSTGRES_PORT", "55432")),
    database="pv1_dev",
)
config = Config(str(root / "backend/alembic.ini"))
engine = create_engine(url)
with engine.connect() as conn:
    tables = set(inspect(conn).get_table_names())
    if tables - {"alembic_version", "scaffold_metadata"}:
        raise SystemExit("Refusing to alter a database with non-scaffold tables.")
command.upgrade(config, "head")
with engine.connect() as conn:
    assert set(inspect(conn).get_table_names()) == {"alembic_version", "scaffold_metadata"}
    assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "0001_scaffold"
    assert conn.scalar(text("SELECT count(*) FROM scaffold_metadata")) == 0
try:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO scaffold_metadata (phase) VALUES ('invalid')"))
except IntegrityError:
    pass
else:
    raise AssertionError("Expected phase0 CHECK constraint to reject invalid phase")
command.downgrade(config, "base")
with engine.connect() as conn:
    assert "scaffold_metadata" not in inspect(conn).get_table_names()
command.upgrade(config, "head")
engine.dispose()
print(
    "PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables."
)
