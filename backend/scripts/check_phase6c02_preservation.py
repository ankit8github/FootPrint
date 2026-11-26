"""Read-only Git-object preservation check. Never regenerates protected assets."""

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "110b3c6353d155943bbf53798f5ec2b623dd3dd0"
HISTORICAL = "d6b2afde058d57e23a75b903b40231dba56a2157"


def git(*args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args], cwd=ROOT
    )


def main() -> None:
    def tree(ref: str) -> dict[str, str]:
        rows = git("ls-tree", "-r", ref).decode().splitlines()
        return {row.split("\t", 1)[1]: row.split()[2] for row in rows}

    original = tree(HISTORICAL)
    baseline = tree(BASE)
    # The 194-file historical tree includes the single previously approved
    # additive phase0.yml CI change in 6C-01; its other 193 blobs are immutable.
    protected = [name for name in original if name != ".github/workflows/phase0.yml"]
    assert len(protected) == 193
    for name in protected:
        assert original[name] == baseline[name], name
    # Preserve ALL base files in this phase, including the original scaffold CI,
    # 6C-01 code/catalog/schema/registry and proposed ADR statuses.
    base_files = list(baseline)
    blobs = (
        subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "hash-object", "--stdin-paths"],
            cwd=ROOT,
            input="\n".join(base_files).encode() + b"\n",
        )
        .decode()
        .splitlines()
    )
    assert len(blobs) == len(base_files)
    for name, blob in zip(base_files, blobs, strict=True):
        # Git's checkout attributes may use CRLF; hash-object applies the same
        # repository filters rather than weakening byte equality arbitrarily.
        assert blob == baseline[name], name
    manifest = ROOT / "backend/experiments/admission_data/manifest.json"
    if manifest.exists():
        print("Admission manifest SHA-256:", hashlib.sha256(manifest.read_bytes()).hexdigest())
    print(f"PASS: 193 historical blobs and all {len(base_files)} base files unchanged")


if __name__ == "__main__":
    main()
