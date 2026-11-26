"""Verify all pre-experiment Git blobs, including earlier evidence, unchanged."""

import subprocess

from experiments.shared_executor import ROOT

REVIEWED = "233620a10abbb6f53b773b853bd41900c62b8b61"


def main() -> None:
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    rows = subprocess.check_output([*git, "ls-tree", "-r", REVIEWED], cwd=ROOT, text=True)
    entries = {r.split("\t", 1)[1]: r.split()[2] for r in rows.splitlines()}
    if len(entries) != 285:
        raise RuntimeError("BASELINE_INVENTORY")
    actual = (
        subprocess.check_output(
            [*git, "hash-object", "--stdin-paths"],
            cwd=ROOT,
            input=("\n".join(entries) + "\n").encode(),
        )
        .decode()
        .splitlines()
    )
    for (path, expected), digest in zip(entries.items(), actual, strict=True):
        if digest != expected:
            raise RuntimeError("PROTECTED_BLOB_CHANGED: " + path)
    print("PASS: all 285 pre-experiment Git blobs unchanged")


if __name__ == "__main__":
    main()
