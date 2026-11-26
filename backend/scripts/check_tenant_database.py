"""Provision NEW disposable synthetic DB, test restricted roles and roundtrip.

Run from backend: uv run --frozen python -m scripts.check_tenant_database
Environment and local/CI setup: docs/PHASE6C02-SECURITY-REPORT.md.
Never reuses scaffold credentials or reads .env.
"""

import subprocess
import sys

from experiments.tenant_db import migrate, provision_fresh, test_engine


def main() -> None:
    bootstrap = test_engine("fp6_bootstrap")
    with bootstrap.begin() as conn:
        provision_fresh(conn)
    bootstrap.dispose()
    migrator = test_engine("fp6_migration_login")
    migrate(migrator)
    result = subprocess.run([sys.executable, "-m", "pytest", "db_tests", "-q"], check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
    # The test ledger includes real committed fictional receipts. Preserve it.
    bootstrap = test_engine("fp6_bootstrap")
    with bootstrap.connect() as conn:
        before = conn.exec_driver_sql(
            "SELECT * FROM fp6_ledger.deletion_journal ORDER BY owner_id,event_id"
        ).all()
        assert before
    migrate(migrator, "base", down=True)
    with bootstrap.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT * FROM fp6_ledger.deletion_journal ORDER BY owner_id,event_id"
            ).all()
            == before
        )
        assert conn.exec_driver_sql("SELECT to_regnamespace('fp6_data')").scalar() is None
    migrate(migrator)
    with bootstrap.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT * FROM fp6_ledger.deletion_journal ORDER BY owner_id,event_id"
            ).all()
            == before
        )
    # Catalog/pool checks on the re-upgraded model; tenant fixtures use new UUIDs.
    result = subprocess.run([sys.executable, "-m", "pytest", "db_tests", "-q"], check=False)
    bootstrap.dispose()
    migrator.dispose()
    if result.returncode:
        raise SystemExit(result.returncode)
    print("PASS: restricted-role SQL, upgrade/downgrade/re-upgrade; ledger retained")


if __name__ == "__main__":
    main()
