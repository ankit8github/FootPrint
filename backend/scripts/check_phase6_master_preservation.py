"""Read-only preservation of every PR #13 blob, including stopped evidence."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "511dfee080d3bcd3c68aaa35ec1474700ff0cf63"


def main() -> None:
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    rows = subprocess.check_output([*git, "ls-tree", "-r", BASE], cwd=ROOT, text=True)
    expected = {row.split("\t", 1)[1]: row.split()[2] for row in rows.splitlines()}
    if len(expected) != 312:
        raise RuntimeError("PRESERVATION_INVENTORY")
    actual = (
        subprocess.check_output(
            [*git, "hash-object", "--stdin-paths"],
            input=("\n".join(expected) + "\n").encode(),
            cwd=ROOT,
        )
        .decode()
        .splitlines()
    )
    for (path, digest), found in zip(expected.items(), actual, strict=True):
        if found != digest:
            raise RuntimeError("PRESERVED_BLOB_CHANGED: " + path)
    print(f"PASS: all {len(expected)} blobs from {BASE} unchanged")


if __name__ == "__main__":
    main()
