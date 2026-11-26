"""Read-only preservation of the entire Phase 6C-03 base, including 6C-02."""

from scripts.check_phase6c02_preservation import ROOT, git
from scripts.check_phase6c02_preservation import main as previous_preservation

BASE = "2038c65554501b7f0a099976ea07b75606cb7ff7"


def main() -> None:
    previous_preservation()
    rows = git("ls-tree", "-r", BASE).decode().splitlines()
    baseline = {row.split("\t", 1)[1]: row.split()[2] for row in rows}
    assert len(baseline) == 270
    for name, blob in baseline.items():
        assert (ROOT / name).is_file(), name
        assert git("hash-object", name).decode().strip() == blob, name
    print("PASS: all 270 Phase 6C-03 baseline blobs unchanged, including schema/RLS/ledger/tests")


if __name__ == "__main__":
    main()
