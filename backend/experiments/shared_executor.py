"""Stopped research prototype; catalog-only. No application imports this module."""

import ctypes
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

from experiments.admission_boundary import model_input
from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.minimized_contract import MAX_BODY, MinimizedBatch, canonical, parse_json

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / ".local/phase6c03-build/worker.mjs"
MAX_OUTPUT = 32 * 1024 * 1024
MEMORY = 256 * 1024 * 1024
DEADLINE = 5.0


class ExecutionRejected(Exception):
    """Fixed safe error; neither evidence nor child diagnostics are exposed."""


def _windows_job(process: subprocess.Popen[bytes]) -> tuple[Any, Any]:
    # A kernel process-commit cap, not merely V8's old-space flag. Attach before
    # supplying evidence; the trusted child initially blocks reading stdin.
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64),
            ("job_time", ctypes.c_int64),
            ("flags", wintypes.DWORD),
            ("minimum", ctypes.c_size_t),
            ("maximum", ctypes.c_size_t),
            ("active", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("r", "w", "o", "rb", "wb", "ob")]

    class Extended(ctypes.Structure):
        _fields_ = [
            ("basic", Basic),
            ("io", IO),
            ("process_limit", ctypes.c_size_t),
            ("job_limit", ctypes.c_size_t),
            ("peak_process", ctypes.c_size_t),
            ("peak_job", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    handle = kernel.OpenProcess(0x0100 | 0x0001, False, process.pid)
    limits = Extended()
    limits.basic.flags = 0x0100 | 0x2000  # PROCESS_MEMORY / KILL_ON_JOB_CLOSE
    limits.process_limit = MEMORY
    try:
        if (
            not job
            or not handle
            or not kernel.SetInformationJobObject(
                job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
            )
            or not kernel.AssignProcessToJobObject(job, handle)
        ):
            raise ExecutionRejected("ISOLATION_UNAVAILABLE")
    except BaseException:
        if job:
            kernel.CloseHandle(job)
        raise
    finally:
        if handle:
            kernel.CloseHandle(handle)
    return kernel, job


def _command() -> list[str]:
    if sys.platform == "win32":
        node = shutil.which("node")
        if not node:
            raise ExecutionRejected("ISOLATION_UNAVAILABLE")
        return [node, "--experimental-permission", f"--allow-fs-read={ARTIFACT}", str(ARTIFACT)]
    # No unverified fallback on another platform. In particular, killing a
    # Docker CLI alone is not evidence that its container was terminated.
    raise ExecutionRejected("ISOLATION_UNAVAILABLE")


def _supervise(raw: bytes) -> tuple[dict[str, Any], dict[str, int | float]]:
    if len(raw) > MAX_BODY:
        raise ExecutionRejected("INPUT_LIMIT")
    # Verify the generated artifact before every launch. Source/lock pins are
    # checked by the trusted build; deployment/artifact signing is out of scope.
    provenance = json.loads(ARTIFACT.with_name("provenance.json").read_bytes())
    if hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() != provenance["worker_sha256"]:
        raise ExecutionRejected("ARTIFACT_MISMATCH")
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ}
    start = time.monotonic()
    process = subprocess.Popen(
        _command(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=ARTIFACT.parent,
    )
    job: tuple[Any, Any] | None = None
    output = bytearray()
    overflow = threading.Event()

    def collect() -> None:
        assert process.stdout is not None
        while block := process.stdout.read(65536):
            if len(output) + len(block) > MAX_OUTPUT:
                overflow.set()
                process.kill()
                return
            output.extend(block)

    def supply() -> None:
        assert process.stdin is not None
        try:
            process.stdin.write(raw)
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    reader = threading.Thread(target=collect)
    writer = threading.Thread(target=supply)
    try:
        if sys.platform == "win32":
            job = _windows_job(process)
        reader.start()
        writer.start()
        process.wait(timeout=max(0.001, DEADLINE - (time.monotonic() - start)))
        reader.join()
        writer.join()
        if overflow.is_set() or process.returncode != 0:
            raise ExecutionRejected("EXECUTION_FAILED")
        decoded = json.loads(output)
        if set(decoded) != {"result", "peak_rss_kib"} or type(decoded["peak_rss_kib"]) is not int:
            raise ExecutionRejected("INVALID_OUTPUT")
        if not 0 < decoded["peak_rss_kib"] <= MEMORY // 1024:
            raise ExecutionRejected("MEMORY_LIMIT")
        if not isinstance(decoded["result"], dict):
            raise ExecutionRejected("INVALID_OUTPUT")
        return decoded["result"], {
            "seconds": round(time.monotonic() - start, 6),
            "peak_rss_kib": decoded["peak_rss_kib"],
            "input_bytes": len(raw),
            "output_bytes": len(output),
        }
    except subprocess.TimeoutExpired:
        raise ExecutionRejected("DEADLINE") from None
    except (ValueError, KeyError, TypeError):
        raise ExecutionRejected("INVALID_OUTPUT") from None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if job:
            job[0].CloseHandle(job[1])
        if reader.ident is not None:
            reader.join()
        if writer.ident is not None:
            writer.join()
        if process.stdout:
            process.stdout.close()
        if process.stdin:
            process.stdin.close()


def execute(batch: MinimizedBatch) -> tuple[dict[str, Any], dict[str, int | float]]:
    """Research only, not a completed executor: admit the pinned synthetic catalog."""
    validated = MinimizedBatch.model_validate(model_input(batch))
    SyntheticRegistry().admit(validated)
    raw = canonical(validated)
    result, metrics = _supervise(raw)
    digest = hashlib.sha256(raw).hexdigest()
    registry = json.loads((DATA / "manifest.json").read_bytes())
    expected = {p["assessment_sha256"] for p in registry["profiles"] if p["digest"] == digest}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    if hashlib.sha256(encoded).hexdigest() not in expected:
        raise ExecutionRejected("SEMANTIC_MISMATCH")
    return result, metrics


def benchmark_only(raw: bytes) -> dict[str, int | float]:
    """Constructed unit fixtures only: never publishes classifications or enrolls input."""
    validated = MinimizedBatch.model_validate(parse_json(raw))
    _, metrics = _supervise(canonical(validated))
    return metrics
