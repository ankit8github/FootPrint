"""Explicit offline synthetic rule revisions; no application/DB/provider integration.

The historical admission class and manifest are untouched. Derived execution is
internal to the separately validated provenance adapter; stress returns metrics.
Windows Job Objects bound trusted children; OS network isolation is NOT claimed.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from experiments.admission_registry import DATA, MANIFEST_SHA256, SyntheticRegistry
from experiments.indexing_validation import IndexedBatch
from experiments.minimized_contract import MAX_BODY, MinimizedBatch, canonical, parse_json
from experiments.shared_executor import (
    DEADLINE,
    MAX_OUTPUT,
    MEMORY,
    ROOT,
    ExecutionRejected,
    _windows_job,
)

PACKAGE_MANIFEST = ROOT / "backend/experiments/rule_packages/manifest.json"
PACKAGE_SHA256 = "7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055"
REVISIONS = ("historical-v1", "indexed-r1")


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: object) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def package(revision: str) -> tuple[Path, str]:
    try:
        if type(revision) is not str or revision not in REVISIONS:
            raise ValueError
        raw = PACKAGE_MANIFEST.read_bytes()
        if hashlib.sha256(raw).hexdigest() != PACKAGE_SHA256:
            raise ValueError
        manifest = json.loads(raw)
        if hashlib.sha256((DATA / "manifest.json").read_bytes()).hexdigest() != MANIFEST_SHA256:
            raise ValueError
        for path, expected in manifest["source_sha256"].items():
            source = (ROOT / path).read_bytes().decode().replace("\r\n", "\n").encode()
            if hashlib.sha256(source).hexdigest() != expected:
                raise ValueError
        for path, expected in manifest["engine_sha256"].items():
            source = (
                (ROOT / "frontend/src" / path).read_bytes().decode().replace("\r\n", "\n").encode()
            )
            if hashlib.sha256(source).hexdigest() != expected:
                raise ValueError
        artifact = ROOT / ".local/phase6c03-packages" / revision / "worker.mjs"
        expected = str(manifest["packages"][revision]["worker_sha256"])
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
            raise ValueError
        return artifact, expected
    except Exception:
        raise ExecutionRejected("PACKAGE_REJECTED") from None


def _json(raw: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def invalid(value: str) -> Any:
        raise ValueError

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _supervise(
    artifact: Path, expected_sha256: str, raw: bytes, cancel: threading.Event | None = None
) -> tuple[dict[str, Any], dict[str, int | float]]:
    """Private process boundary; test fixtures may exercise it, never caller paths."""
    if sys.platform != "win32":
        raise ExecutionRejected("ISOLATION_UNAVAILABLE")
    if len(raw) > MAX_BODY:
        raise ExecutionRejected("INPUT_LIMIT")
    if cancel is not None and cancel.is_set():
        raise ExecutionRejected("CANCELLED")
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_sha256:
        raise ExecutionRejected("ARTIFACT_MISMATCH")
    node = shutil.which("node")
    if node is None:
        raise ExecutionRejected("NODE_UNAVAILABLE")
    output, diagnostics = bytearray(), bytearray()
    overflow, pipe_failure = threading.Event(), threading.Event()
    started = time.perf_counter()
    process = subprocess.Popen(
        [
            node,
            "--no-warnings",
            "--experimental-permission",
            f"--allow-fs-read={artifact}",
            str(artifact),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=artifact.parent,
        env={k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ},
    )
    job: tuple[Any, Any] | None = None

    def read(pipe: Any, target: bytearray, limit: int) -> None:
        try:
            while block := pipe.read(65536):
                if len(target) + len(block) > limit:
                    overflow.set()
                    process.kill()
                    return
                target.extend(block)
        except (OSError, ValueError):
            pipe_failure.set()

    def write() -> None:
        try:
            assert process.stdin
            process.stdin.write(raw)
            process.stdin.close()
        except (OSError, ValueError):
            pipe_failure.set()

    threads = [
        threading.Thread(target=read, args=(process.stdout, output, MAX_OUTPUT), daemon=True),
        threading.Thread(target=read, args=(process.stderr, diagnostics, 8192), daemon=True),
        threading.Thread(target=write, daemon=True),
    ]
    try:
        job = _windows_job(process)
        for thread in threads:
            thread.start()
        while process.poll() is None:
            if cancel is not None and cancel.is_set():
                raise ExecutionRejected("CANCELLED")
            remaining = DEADLINE - (time.perf_counter() - started)
            if remaining <= 0:
                raise ExecutionRejected("DEADLINE")
            try:
                process.wait(timeout=min(0.02, remaining))
            except subprocess.TimeoutExpired:
                pass
        child_wall = time.perf_counter() - started
        # Close the job before joining pipes: descendants cannot keep them open.
        job[0].CloseHandle(job[1])
        job = None
        for thread in threads:
            thread.join(timeout=1)
        if any(thread.is_alive() for thread in threads):
            raise ExecutionRejected("PIPE_CLEANUP_FAILED")
        if overflow.is_set():
            raise ExecutionRejected("OUTPUT_LIMIT")
        if process.returncode or pipe_failure.is_set():
            raise ExecutionRejected("EXECUTION_FAILED")
        if cancel is not None and cancel.is_set():
            raise ExecutionRejected("CANCELLED")
        decoded = _json(bytes(output))
        keys = set(decoded)
        if keys not in ({"result", "peak_rss_kib"}, {"result", "peak_rss_kib", "eligible_actions"}):
            raise ValueError
        peak = decoded["peak_rss_kib"]
        if diagnostics:
            measurement = _json(bytes(diagnostics))
            if set(measurement) != {"peak_rss_kib"}:
                raise ValueError
            peak = measurement["peak_rss_kib"]
        if type(peak) is not int or not 0 < peak <= MEMORY // 1024:
            raise ExecutionRejected("MEMORY_LIMIT")
        if type(decoded["result"]) is not dict:
            raise ValueError
        return decoded, {
            "child_seconds": child_wall,
            "supervisor_seconds": time.perf_counter() - started,
            "peak_rss_kib": peak,
            "input_bytes": len(raw),
            "output_bytes": len(output),
            "child_pid": process.pid,
            "child_exit": process.returncode,
        }
    except (ValueError, KeyError, TypeError, RecursionError):
        raise ExecutionRejected("INVALID_OUTPUT") from None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if job:
            job[0].CloseHandle(job[1])
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=1)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe:
                pipe.close()


def _execute(
    raw: bytes, revision: str, cancel: threading.Event | None = None
) -> tuple[dict[str, Any], dict[str, int | float]]:
    begin = time.perf_counter()
    if type(raw) is not bytes or len(raw) > MAX_BODY:
        raise ExecutionRejected("INPUT_LIMIT")
    artifact, expected = package(revision)
    validator = IndexedBatch if revision == "indexed-r1" else MinimizedBatch
    batch = validator.model_validate(parse_json(raw))
    validated = time.perf_counter()
    payload, metrics = _supervise(artifact, expected, canonical(batch), cancel)
    result = payload["result"]
    graph = result["discovery"]
    if (
        set(result)
        != {
            "schema_version",
            "ruleset_version",
            "context_version",
            "synthetic_only",
            "discovery",
            "context_evidence",
            "assessments",
        }
        or result["schema_version"] != "phase4-assessment-v1"
        or result["ruleset_version"] != "sensitivity_rules_v1"
        or result["context_version"] != "email_context_v1"
        or result["synthetic_only"] is not True
        or graph["sources"] != [s.model_dump() for s in batch.sources]
        or graph["observations"]
        != [{**o.model_dump(), "evidence_state": "observed"} for o in batch.observations]
        or graph["excluded"] != [e.model_dump() for e in batch.excluded]
        or graph["duplicate_groups"] != batch.duplicate_groups
        or result["context_evidence"] != [c.model_dump() for c in batch.contexts]
    ):
        raise ExecutionRejected("RESULT_MISMATCH")
    metrics.update(validation_seconds=validated - begin, total_seconds=time.perf_counter() - begin)
    return payload, metrics


def execute_catalog(
    raw: bytes, revision: str = "indexed-r1"
) -> tuple[dict[str, Any], dict[str, int | float]]:
    """Exact existing catalog only; no subclass or new model admission policy."""
    model = MinimizedBatch.model_validate(parse_json(raw))
    SyntheticRegistry().admit(model)
    payload, metrics = _execute(canonical(model), revision)
    registry = json.loads((DATA / "manifest.json").read_bytes())
    key = hashlib.sha256(canonical(model)).hexdigest()
    profiles = [p for p in registry["profiles"] if p["digest"] == key]
    if digest(payload["result"]) not in {p["assessment_sha256"] for p in profiles}:
        raise ExecutionRejected("SEMANTIC_MISMATCH")
    if digest(payload["result"]["discovery"]) not in {p["discovery_sha256"] for p in profiles}:
        raise ExecutionRejected("SEMANTIC_MISMATCH")
    return payload, metrics


def benchmark_only(raw: bytes) -> dict[str, int | float | str]:
    """Constructed model capacity only; never exposes findings or enrolls inputs."""
    payload, metrics = _execute(raw, "indexed-r1")
    return {
        **metrics,
        "result_sha256": digest(payload["result"]),
        "discovery_sha256": digest(payload["result"]["discovery"]),
    }
