"""Export deterministic API schema; --check detects stale committed contracts."""

import argparse
import json
from pathlib import Path

from app.main import app

target = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"
content = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
if args.check:
    if not target.exists() or target.read_text(encoding="utf-8") != content:
        raise SystemExit("OpenAPI is stale: run the contract generation commands in README.")
else:
    target.write_text(content, encoding="utf-8")
