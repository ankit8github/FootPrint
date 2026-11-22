"""Reviewed Phase 0 metadata only; deliberately does not install candidate PV1 DDL.

Review: docs/DECISIONS.md, ADR-002. No personal-data storage or pgcrypto extension.
Downgrade removes only this migration's empty scaffold metadata table.
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_scaffold"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scaffold_metadata",
        sa.Column("phase", sa.String(16), primary_key=True),
        sa.CheckConstraint("phase = 'phase0'", name="ck_scaffold_phase0"),
    )


def downgrade() -> None:
    op.drop_table("scaffold_metadata")
