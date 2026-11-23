"""Export the separate Phase 2 normalized boundary schema."""

import argparse
import json
from pathlib import Path

from app.phase2 import boundary

target = Path(__file__).resolve().parents[2] / "frontend/phase2-openapi.json"
content = json.dumps(boundary.openapi(), indent=2, sort_keys=True) + "\n"
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
if parser.parse_args().check:
    if not target.exists() or target.read_text(encoding="utf-8") != content:
        raise SystemExit("Phase 2 OpenAPI is stale")
else:
    target.write_text(content, encoding="utf-8", newline="\n")
