"""Bounded evidence-only profiling; existing rules, runner and limits stay unchanged."""

import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from typing import Any

from experiments.indexing_validation import IndexedBatch
from experiments.minimized_contract import MAX_BODY, MinimizedBatch, canonical, parse_json
from experiments.shared_executor import DEADLINE, MAX_OUTPUT, MEMORY, ROOT, _windows_job

ARTIFACTS = {
    v: ROOT / f".local/phase6c03-indexing-build/{v}/worker.mjs" for v in ("baseline", "indexed")
}
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


def measure(raw: bytes, variant: str = "indexed") -> dict[str, Any]:
    """No classification is returned, even on success; only metrics and result hashes."""
    profile = ARTIFACTS[variant]
    validator = IndexedBatch if variant == "indexed" else MinimizedBatch
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
    batch = validator.model_validate(parse_json(raw))
    validated = time.perf_counter()
    encoded = canonical(batch)
    input_ready = time.perf_counter()
    provenance = json.loads(profile.with_name("provenance.json").read_bytes())
    if hashlib.sha256(profile.read_bytes()).hexdigest() != provenance["worker_sha256"]:
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
            f"--allow-fs-read={profile}",
            str(profile),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ},
        cwd=profile.parent,
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
    support_sha = None
    if status == "PASS":
        graph = decoded["result"]["discovery"]
        support_sha = digest(
            {
                k: graph[k]
                for k in (
                    "relationships",
                    "relationship_evidence",
                    "duplicate_groups",
                    "conflicts",
                    "unresolved",
                )
            }
        )
    done = time.perf_counter()
    return {
        "status": status,
        "variant": variant,
        "support_sha256": support_sha,
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
