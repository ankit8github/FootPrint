"""Bounded evidence-only profiling; existing rules, runner and limits stay unchanged."""

import argparse
import ctypes
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import uuid
from typing import Any

from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.minimized_contract import MAX_BODY, MinimizedBatch, canonical, parse_json
from experiments.session_store import Denied
from experiments.shared_executor import DEADLINE, MAX_OUTPUT, MEMORY, ROOT, _supervise, _windows_job
from scripts.benchmark_shared_rules import fixture

PROFILE = ROOT / ".local/phase6c03-investigation-build/worker.mjs"
KINDS = ("primary_account", "commercial_distinct", "unresolved", "duplicates")
PHASES = (
    "entered",
    "rules_loaded",
    "read",
    "parse",
    "prepare",
    "link",
    "assess",
    "assemble",
    "serialize",
    "write",
)


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def child_cpu(process: subprocess.Popen[bytes]) -> float | None:
    if sys.platform != "win32":
        return None
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.c_void_p] * 4)]
    values = [wintypes.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(
        int(vars(process)["_handle"]), *(ctypes.byref(value) for value in values)
    ):
        return None
    return sum((v.dwHighDateTime << 32) + v.dwLowDateTime for v in values[2:]) / 10_000_000


def measure(raw: bytes) -> dict[str, Any]:
    """No classification is returned, even on success; only metrics and result hashes."""
    if sys.platform != "win32" or (DEADLINE, MEMORY, MAX_BODY, MAX_OUTPUT) != (
        5.0,
        256 * 1024 * 1024,
        8 * 1024 * 1024,
        32 * 1024 * 1024,
    ):
        raise RuntimeError("UNSUPPORTED_BOUNDARY")
    if len(raw) > MAX_BODY:
        raise RuntimeError("INPUT_LIMIT")
    begin, begin_cpu = time.perf_counter(), time.process_time()
    batch = MinimizedBatch.model_validate(parse_json(raw))
    validated = time.perf_counter()
    encoded = canonical(batch)
    input_ready = time.perf_counter()
    provenance = json.loads(PROFILE.with_name("provenance.json").read_bytes())
    if hashlib.sha256(PROFILE.read_bytes()).hexdigest() != provenance["worker_sha256"]:
        raise RuntimeError("ARTIFACT_MISMATCH")
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("NODE_UNAVAILABLE")
    launch = time.perf_counter()
    process = subprocess.Popen(
        [
            node,
            "--no-warnings",
            "--experimental-permission",
            f"--allow-fs-read={PROFILE}",
            str(PROFILE),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ},
        cwd=PROFILE.parent,
    )
    output = bytearray()
    events: list[dict[str, Any]] = []
    overflow = threading.Event()
    protocol_error = threading.Event()
    status = "PASS"
    job: tuple[Any, Any] | None = None
    first_event: float | None = None
    supplied: float | None = None

    def collect() -> None:
        assert process.stdout is not None
        while block := process.stdout.read(65536):
            if len(output) + len(block) > MAX_OUTPUT:
                overflow.set()
                process.kill()
                return
            output.extend(block)

    def diagnostics() -> None:
        nonlocal first_event
        assert process.stderr is not None
        size = 0
        while line := process.stderr.readline(2048):
            size += len(line)
            if size > 16_384:
                protocol_error.set()
                process.kill()
                return
            try:
                event = json.loads(line)
                if event["phase"] not in (*PHASES, "failed") or len(events) >= 11:
                    raise ValueError
                if first_event is None:
                    first_event = time.perf_counter() - launch
                events.append(event)
            except (ValueError, KeyError, TypeError):
                protocol_error.set()

    def supply() -> None:
        nonlocal supplied
        assert process.stdin is not None
        try:
            process.stdin.write(encoded)
            process.stdin.close()
            supplied = time.perf_counter() - launch
        except (BrokenPipeError, OSError):
            pass

    readers = [threading.Thread(target=collect), threading.Thread(target=diagnostics)]
    writer = threading.Thread(target=supply)
    try:
        job = _windows_job(process)
        for thread in [*readers, writer]:
            thread.start()
        try:
            process.wait(timeout=max(0.001, DEADLINE - (time.perf_counter() - launch)))
        except subprocess.TimeoutExpired:
            status = "DEADLINE"
            process.kill()
            process.wait()
        exited = time.perf_counter()
        cpu = child_cpu(process)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if job:
            job[0].CloseHandle(job[1])
        for thread in [*readers, writer]:
            if thread.ident is not None:
                thread.join()
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe:
                pipe.close()
    collected = time.perf_counter()
    if status == "PASS" and (
        process.returncode
        or overflow.is_set()
        or protocol_error.is_set()
        or [e["phase"] for e in events] != list(PHASES)
    ):
        status = "CHILD_OR_PROTOCOL_FAILURE"
    peak = max((e["peak_rss_kib"] for e in events), default=None)
    if status == "PASS" and (peak is None or peak > MEMORY // 1024):
        status = "MEMORY_LIMIT"
    result_sha: str | None = None
    discovery_sha: str | None = None
    if status == "PASS":
        decoded = json.loads(output)
        result_sha = digest(decoded["result"])
        discovery_sha = digest(decoded["result"]["discovery"])
    done = time.perf_counter()
    return {
        "status": status,
        "input_bytes": len(encoded),
        "stdout_bytes_observed": len(output),
        "result_sha256": result_sha,
        "discovery_sha256": discovery_sha,
        "input_sha256": hashlib.sha256(encoded).hexdigest(),
        "validation_seconds_outside_child_budget": validated - begin,
        "canonical_input_seconds_outside_child_budget": input_ready - validated,
        "child_wall_seconds_including_launch_and_kill": exited - launch,
        "child_process_cpu_seconds": cpu,
        "startup_to_first_metric_seconds": first_event,
        "input_supplied_seconds": supplied,
        "collect_after_exit_seconds": collected - exited,
        "parent_decode_and_hash_seconds": done - collected,
        "supervisor_wall_seconds": done - launch,
        "total_case_seconds_including_validation": done - begin,
        "parent_cpu_seconds_including_validation": time.process_time() - begin_cpu,
        "peak_rss_kib": peak,
        "peak_rss_scope": "final_marker" if status == "PASS" else "last_phase_lower_bound",
        "full_output_bytes": len(output) if status == "PASS" else None,
        "phases": events,
    }


def catalog_inventory(registry: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for entry in registry["entries"]:
        batch = MinimizedBatch.model_validate_json(
            (DATA / (entry["digest"] + ".json")).read_bytes()
        )
        rows.append(
            {
                "digest": entry["digest"],
                "sources": len(batch.sources),
                "rows": sum(s.record_count for s in batch.sources),
                "observations": len(batch.observations),
                "aliases": len(batch.commercial_groups),
                "input_bytes": entry["bytes"],
            }
        )
    return {
        "entries": rows,
        "maxima": {
            k: max(row[k] for row in rows)
            for k in ("sources", "rows", "observations", "aliases", "input_bytes")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("catalog", "matrix", "full", "all"), default="all")
    args = parser.parse_args()
    out = ROOT / (".local/phase6c03-investigation-" + uuid.uuid4().hex)
    out.mkdir()
    registry = json.loads((DATA / "manifest.json").read_bytes())
    gate = SyntheticRegistry()
    records: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "reviewed_head": "5e1cd681d4d19193f4a2c4161b9e1b78b77de139",
        "mode": args.mode,
        "platform": platform.platform(),
        "python": sys.version,
        "limits": {
            "child_wall_seconds": DEADLINE,
            "committed_memory_bytes": MEMORY,
            "input_bytes": MAX_BODY,
            "output_bytes": MAX_OUTPUT,
        },
        "artifact": json.loads(PROFILE.with_name("provenance.json").read_bytes()),
        "catalog": catalog_inventory(registry),
        "runs": records,
    }
    print("Evidence:", out, flush=True)

    def save() -> None:
        (out / "measurements.json").write_text(json.dumps(receipt, indent=2) + "\n")

    previous: dict[str, str] = {}

    def run(label: str, raw: bytes, expected: dict[str, Any] | None = None) -> None:
        row = {"label": label, **measure(raw)}
        if row["status"] == "PASS":
            if expected is not None and (
                row["result_sha256"] != expected["assessment_sha256"]
                or row["discovery_sha256"] != expected["discovery_sha256"]
            ):
                row["status"] = "SEMANTIC_MISMATCH"
            if (
                row["input_sha256"] in previous
                and previous[row["input_sha256"]] != row["result_sha256"]
            ):
                row["status"] = "SEMANTIC_MISMATCH"
            previous[row["input_sha256"]] = row["result_sha256"]
        records.append(row)
        save()
        print(
            json.dumps(
                {
                    k: row[k]
                    for k in (
                        "label",
                        "status",
                        "child_wall_seconds_including_launch_and_kill",
                        "child_process_cpu_seconds",
                        "peak_rss_kib",
                        "input_bytes",
                        "full_output_bytes",
                    )
                }
            ),
            flush=True,
        )
        if row["status"] != "PASS":
            raise SystemExit("STOP: " + row["status"])

    if args.mode in ("catalog", "all"):
        for entry in registry["entries"]:
            raw = (DATA / (entry["digest"] + ".json")).read_bytes()
            gate.admit(MinimizedBatch.model_validate_json(raw))
            expected = next(p for p in registry["profiles"] if p["digest"] == entry["digest"])
            run("catalog-" + entry["digest"][:8], raw, expected)
    if args.mode in ("matrix", "all"):
        for count in (20, 1000, 4000):
            for kind in KINDS:
                raw = fixture(kind, count)
                for repeat in range(2):
                    run(f"{kind}-{count}-r{repeat + 1}", raw)
                if count == 1000:
                    baseline, metrics = _supervise(
                        canonical(MinimizedBatch.model_validate(parse_json(raw)))
                    )
                    same = digest(baseline) == records[-1]["result_sha256"]
                    records.append(
                        {
                            "label": f"baseline-{kind}-{count}",
                            "same_result_sha256": same,
                            "metrics": metrics,
                        }
                    )
                    save()
                    if not same:
                        raise SystemExit("STOP: SEMANTIC_MISMATCH")
    if args.mode in ("full", "all"):
        # Complete other families first; a commercial deadline stops, never retries.
        for kind in ("primary_account", "unresolved", "duplicates", "commercial_distinct"):
            raw = fixture(kind)
            admission_start = time.perf_counter()
            batch = MinimizedBatch.model_validate(parse_json(raw))
            try:
                gate.admit(batch)
            except Denied as error:
                receipt.setdefault("stress_admission", {})[kind] = {
                    "denied_status": error.status,
                    "model_valid": True,
                    "seconds_including_model_revalidation": time.perf_counter() - admission_start,
                }
            else:
                raise RuntimeError("UNEXPECTED_STRESS_ADMISSION")
            run(f"{kind}-10000", raw)
    save()


if __name__ == "__main__":
    main()
