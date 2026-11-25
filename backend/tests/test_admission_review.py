"""Review regression cases; no qualified independent human approval is implied."""

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from admission_test_support import DIGESTS, envelope, harness

from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.minimized_contract import MAX_BODY, AdmissionEnvelope
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import Denied


@pytest.mark.parametrize(
    "case",
    [
        "version",
        "epoch_bool",
        "revision_bool",
        "epoch_string",
        "revision_float",
        "missing_version",
        "missing_batch",
    ],
)
def test_direct_method_revalidates_unvalidated_envelope_instances(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            assert f.authority
            principal = f.authority.resolve(a.cookies[SESSION_COOKIE])
            valid = AdmissionEnvelope.model_validate(envelope())
            if case.startswith("missing_"):
                values = {
                    "consent_version": valid.consent_version,
                    "consent_epoch": 1,
                    "expected_revision": 1,
                    "batch": valid.batch,
                }
                values.pop("consent_version" if case == "missing_version" else "batch")
                invalid = AdmissionEnvelope.model_construct(**values)  # type: ignore[arg-type]
            else:
                field, value = {
                    "version": ("consent_version", "unsupported"),
                    "epoch_bool": ("consent_epoch", True),
                    "revision_bool": ("expected_revision", True),
                    "epoch_string": ("consent_epoch", "1"),
                    "revision_float": ("expected_revision", 1.0),
                }[case]
                invalid = valid.model_copy(update={field: value})
            before = dict(f.controls)
            with pytest.raises(Denied) as error:
                await f.validate(principal, invalid, f.csrf(principal))
            assert error.value.status == 422 and f.controls == before

    asyncio.run(run())


@pytest.mark.parametrize("denial", ["principal", "consent"])
def test_direct_method_denies_before_serializing_data(
    denial: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with harness(consent=denial != "consent") as (f, a, _, _):
            assert f.authority
            principal = f.authority.resolve(a.cookies[SESSION_COOKIE])
            token = f.csrf(principal)
            data = AdmissionEnvelope.model_validate(envelope())

            def forbidden(*args: Any, **kwargs: Any) -> Any:
                raise AssertionError("data work before authorization")

            monkeypatch.setattr(AdmissionEnvelope, "model_dump", forbidden)
            with pytest.raises(Denied) as error:
                await f.validate(None if denial == "principal" else principal, data, token)  # type: ignore[arg-type]
            assert error.value.status == (401 if denial == "principal" else 403)

    asyncio.run(run())


@pytest.mark.parametrize("artifact", ["manifest", "batch"])
def test_corrupt_oversized_catalog_reads_are_bounded_before_rejection(
    artifact: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import experiments.admission_registry as module

    for source in DATA.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    target = tmp_path / ("manifest.json" if artifact == "manifest" else DIGESTS[0] + ".json")
    with target.open("wb") as stream:
        stream.seek(MAX_BODY + 1024)
        stream.write(b"SYNTHETIC")
    reads: list[tuple[str, int]] = []
    original_open = Path.open

    @contextmanager
    def bounded_open(path: Path, *args: Any, **kwargs: Any) -> Iterator[Any]:
        with original_open(path, *args, **kwargs) as handle:

            class Reader:
                def read(self, size: int = -1) -> bytes:
                    assert 0 < size <= MAX_BODY + 2, "unbounded artifact read"
                    reads.append((path.name, size))
                    result = handle.read(size)
                    assert isinstance(result, bytes)
                    return result

            yield Reader()

    monkeypatch.setattr(module, "DATA", tmp_path)
    monkeypatch.setattr(Path, "open", bounded_open)
    with pytest.raises(Denied) as error:
        SyntheticRegistry()
    assert error.value.status == 503
    assert reads[-1] == (target.name, MAX_BODY + (1 if artifact == "manifest" else 2))
