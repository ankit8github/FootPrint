"""Separately invoked synthetic provenance graph; no URL or offline execution."""

from alembic import context

from experiments.provenance_schema import require_candidate_database

connection = context.config.attributes.get("connection")
if connection is None or context.is_offline_mode():
    raise RuntimeError("Recognized fresh synthetic controller connection required")
require_candidate_database(connection)
context.configure(
    connection=connection,
    version_table="provenance_alembic_version",
    version_table_schema="fp6_guard",
)
with context.begin_transaction():
    context.run_migrations()
