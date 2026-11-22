from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_reviewed_initial_migration_offline_upgrade_and_downgrade() -> None:
    output = StringIO()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE scaffold_metadata" in sql
    assert "CHECK (phase = 'phase0')" in sql
    assert "CREATE TABLE users" not in sql
    assert "CREATE TABLE observations" not in sql
    output.truncate(0)
    output.seek(0)
    command.downgrade(config, "0001_scaffold:base", sql=True)
    assert "DROP TABLE scaffold_metadata" in output.getvalue()
