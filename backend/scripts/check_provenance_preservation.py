"""Read-only verification of every pre-candidate blob; no adapter imports."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = "511dfee080d3bcd3c68aaa35ec1474700ff0cf63"
BASE = "2038c65554501b7f0a099976ea07b75606cb7ff7"


def main() -> None:
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    for ref, count in ((PREFLIGHT, 312), (BASE, 270)):
        rows = subprocess.check_output([*git, "ls-tree", "-r", ref], cwd=ROOT, text=True)
        expected = {r.split("\t", 1)[1]: r.split()[2] for r in rows.splitlines()}
        if len(expected) != count:
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
            if digest != found:
                raise RuntimeError("PRESERVED_BLOB_CHANGED: " + path)
        print(f"PASS: all {count} blobs from {ref} unchanged")


if __name__ == "__main__":
    main()
