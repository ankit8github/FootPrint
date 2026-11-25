"""Pinned offline whole-envelope catalog. Never enrolls caller supplied profiles."""

import hashlib
from pathlib import Path
from types import MappingProxyType

from experiments.minimized_contract import MAX_BODY, MinimizedBatch, canonical, parse_json
from experiments.session_store import Denied

DATA = Path(__file__).with_name("admission_data")
MANIFEST_SHA256 = "333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699"


def _bounded_file(path: Path, limit: int) -> bytes:
    # A corrupt trusted artifact must not be read without a bound before rejection.
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("invalid registry")
    return raw


class SyntheticRegistry:
    def __init__(self) -> None:
        try:
            raw = _bounded_file(DATA / "manifest.json", MAX_BODY)
            if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
                raise ValueError
            manifest = parse_json(raw)
            if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list):
                raise ValueError
            entries: dict[str, bytes] = {}
            for entry in manifest["entries"]:
                digest = entry["digest"]
                if (
                    type(digest) is not str
                    or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                ):
                    raise ValueError
                stored = _bounded_file(DATA / (digest + ".json"), MAX_BODY + 1)
                if not stored.endswith(b"\n"):
                    raise ValueError
                encoded = stored[:-1]
                batch = MinimizedBatch.model_validate(parse_json(encoded))
                if (
                    canonical(batch) != encoded
                    or len(encoded) != entry["bytes"]
                    or hashlib.sha256(encoded).hexdigest() != digest
                    or digest in entries
                ):
                    raise ValueError
                entries[digest] = encoded
            if not entries or len(entries) != 32:
                raise ValueError
            self.__entries = MappingProxyType(entries)
        except Exception:
            raise Denied(503) from None

    def admit(self, batch: MinimizedBatch) -> None:
        try:
            if type(batch) is not MinimizedBatch:
                raise Denied(422)
            # Revalidate a possibly trusted-Python-mutated nested list, too.
            encoded = canonical(MinimizedBatch.model_validate(batch.model_dump()))
            digest = hashlib.sha256(encoded).hexdigest()
            if self.__entries.get(digest) != encoded:
                raise Denied(422)
        except Denied:
            raise
        except Exception:
            raise Denied(503) from None
