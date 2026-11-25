"""Offline proposed schema export/check, never added to normal OpenAPI."""

import argparse
import json

from experiments.admission_registry import DATA
from experiments.minimized_contract import AdmissionEnvelope


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = DATA / "minimized-evidence-v1.schema.json"
    encoded = (
        json.dumps(AdmissionEnvelope.model_json_schema(), indent=2, sort_keys=True) + "\n"
    ).encode()
    if args.check:
        if target.read_bytes() != encoded:
            raise SystemExit("Proposed minimized schema differs")
    else:
        target.write_bytes(encoded)


if __name__ == "__main__":
    main()
