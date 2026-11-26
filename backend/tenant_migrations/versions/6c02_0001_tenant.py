"""Add the synthetic-only tenant model; preserve ledger on disposable rollback."""

from pathlib import Path

from alembic import op
from sqlalchemy import text

from experiments.tenant_db import require_disposable

revision = "6c02_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    require_disposable(op.get_bind())
    ddl = Path(__file__).with_name("6c02_0001.sql").read_text(encoding="utf-8")
    op.get_bind().execute(text(ddl))


def downgrade() -> None:
    # This track is not a production migration tool. The marker and exact object
    # inventory are rechecked, even when Alembic is invoked without the runner.
    require_disposable(op.get_bind())
    for schema in ("fp6_data", "fp6_auth", "fp6_reference"):
        op.execute(f"DROP SCHEMA {schema} CASCADE")
    # fp6_context + fp6_ledger deliberately survive, including forced tenant RLS.
    # No journal row is removed or restored to undo a deletion.
