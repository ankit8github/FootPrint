"""Isolated synthetic track. Never reads .env or connects to the scaffold DB."""

from alembic import context

from experiments.tenant_db import require_disposable

connection = context.config.attributes.get("connection")
if connection is None or context.is_offline_mode():
    raise RuntimeError("Use scripts.check_tenant_database on a recognized synthetic database")
require_disposable(connection)
context.configure(
    connection=connection,
    version_table="tenant_alembic_version",
    version_table_schema="fp6_guard",
)
with context.begin_transaction():
    context.run_migrations()
