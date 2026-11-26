"""Add generation-scoped immutable implementation bindings; never infer history."""

from pathlib import Path

from alembic import op
from sqlalchemy import text

from experiments.provenance_schema import require_candidate_database

revision = "c03_comp01_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    require_candidate_database(op.get_bind())
    sql = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    op.get_bind().execute(text(sql))


def downgrade() -> None:
    require_candidate_database(op.get_bind())
    # Constraint validation scans every physical row, including under FORCE RLS.
    # Do not use an owner SELECT count(*) that could silently see zero rows.
    # ACCESS EXCLUSIVE locks make the empty check and DDL one atomic operation.
    op.execute("LOCK TABLE fp6_data.generations, fp6_data.generation_implementations")
    op.execute(
        "ALTER TABLE fp6_data.generation_implementations "
        "ADD CONSTRAINT rollback_requires_no_provenance CHECK (false) NOT VALID"
    )
    op.execute(
        "ALTER TABLE fp6_data.generation_implementations "
        "VALIDATE CONSTRAINT rollback_requires_no_provenance"
    )
    op.execute("ALTER TABLE fp6_data.generations DROP CONSTRAINT implementation_required")
    op.execute("DROP TRIGGER bind_implementation ON fp6_data.generations")
    op.execute("DROP TABLE fp6_data.generation_implementations")
    op.execute("DROP TABLE fp6_reference.implementation_packages")
    op.execute("DROP FUNCTION fp6_context.bind_implementation()")
    op.execute("DROP FUNCTION fp6_context.immutable_implementation()")
