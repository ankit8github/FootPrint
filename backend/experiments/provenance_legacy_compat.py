"""Explicit test-only catalog adaptation for the unchanged 434 legacy cases.

Loaded only with pytest -p experiments.provenance_legacy_compat. Three imported
bindings change: the exact expected table inventory, and the guard references in
the legacy fixture/test modules. No fixture values, ownership policy, assertion,
admission predicate or legacy source file is changed. The candidate guard is
strict about the complete base plus named additions and revision. Pristine base
runs do not load this plugin.
"""

from experiments.provenance_schema import ADDED_TABLES, require_candidate_database
from experiments.tenant_db import EXPECTED_TABLES


def pytest_configure() -> None:
    from db_tests import conftest, test_tenant_security

    vars(conftest)["require_disposable"] = require_candidate_database
    vars(test_tenant_security)["require_disposable"] = require_candidate_database
    vars(test_tenant_security)["EXPECTED_TABLES"] = EXPECTED_TABLES | ADDED_TABLES
