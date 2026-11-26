"""Real local processes, fixed synthetic bytes, unchanged executor/resource limits.

These tests exercise the private supervisor, not admission or a durable adapter.
The network acceptance assertion is intentionally strict: reachable loopback is a
failed no-network gate. No xfail, fallback, live destination or policy waiver.
"""

import ctypes
import hashlib
import json
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from experiments import versioned_executor as executor
from experiments.minimized_contract import MAX_BODY
from experiments.shared_executor import (
    DEADLINE,
    MAX_OUTPUT,
    MEMORY,
    ExecutionRejected,
    _windows_job,
)

WINDOWS = pytest.mark.skipif(sys.platform != "win32", reason="Actual Windows Job Object test")
VALID = '{"result":{},"peak_rss_kib":1}'


@pytest.fixture
def children(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[subprocess.Popen[bytes]]]:
    original = subprocess.Popen
    processes: list[subprocess.Popen[bytes]] = []

    def spawn(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", spawn)
    yield processes
    # A rejection must not leave its real root process alive. No test cleanup is
    # used to turn a leaked root into a passing result.
    assert all(p.poll() is not None for p in processes), "ROOT_PROCESS_LEAK"
    print("root_exits=" + json.dumps([(p.pid, p.returncode) for p in processes]))


@pytest.fixture
def supervise(tmp_path: Path) -> Callable[..., tuple[dict[str, Any], dict[str, int | float]]]:
    serial = 0

    def invoke(
        code: str,
        raw: bytes = b"{}",
        cancel: threading.Event | None = None,
        read_input: bool = True,
    ) -> tuple[dict[str, Any], dict[str, int | float]]:
        nonlocal serial
        serial += 1
        artifact = tmp_path / f"synthetic-{serial}.mjs"
        # Block on stdin before doing any work, as the trusted package does.
        source = ("for await (const chunk of process.stdin) {}\n" if read_input else "") + code
        artifact.write_text(source, encoding="utf-8")
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        started = time.perf_counter()
        try:
            return executor._supervise(artifact, expected, raw, cancel)
        finally:
            print(f"supervisor_seconds={time.perf_counter() - started:.6f}")

    return invoke


def test_limits_unchanged() -> None:
    assert (DEADLINE, MEMORY, MAX_BODY, MAX_OUTPUT) == (
        5.0,
        256 * 1024 * 1024,
        8 * 1024 * 1024,
        32 * 1024 * 1024,
    )


def test_unsupported_platform_fails_before_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, children: list[subprocess.Popen[bytes]]
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(ExecutionRejected, match="^ISOLATION_UNAVAILABLE$"):
        executor._supervise(tmp_path / "never-read.mjs", "not-a-digest", b"{}")
    assert not children


@WINDOWS
def test_prelaunch_guards(tmp_path: Path, children: list[subprocess.Popen[bytes]]) -> None:
    artifact = tmp_path / "never-read.mjs"
    with pytest.raises(ExecutionRejected, match="^INPUT_LIMIT$"):
        executor._supervise(artifact, "not-a-digest", b"x" * (MAX_BODY + 1))
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(ExecutionRejected, match="^CANCELLED$"):
        executor._supervise(artifact, "not-a-digest", b"{}", cancelled)
    artifact.write_text("", encoding="utf-8")
    with pytest.raises(ExecutionRejected, match="^ARTIFACT_MISMATCH$"):
        executor._supervise(artifact, "0" * 64, b"{}")
    assert not children


@WINDOWS
@pytest.mark.parametrize("size", [0, MAX_BODY])
def test_valid_empty_result_and_exact_input_limit(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], size: int
) -> None:
    payload, metrics = supervise(f"process.stdout.write({json.dumps(VALID)});", b" " * size)
    assert payload == {"result": {}, "peak_rss_kib": 1}
    assert metrics["input_bytes"] == size and metrics["child_exit"] == 0
    assert children[-1].poll() == 0


@WINDOWS
@pytest.mark.parametrize(
    "wire",
    [
        "",
        "{",
        VALID[:-1],
        VALID + VALID,
        "null",
        "[]",
        "true",
        "123",
        '{"result":{},"result":{},"peak_rss_kib":1}',
        '{"result":{"a":1,"a":2},"peak_rss_kib":1}',
        '{"result":{},"peak_rss_kib":NaN}',
        '{"result":{},"peak_rss_kib":Infinity}',
        '{"result":[],"peak_rss_kib":1}',
        '{"result":{},"peak_rss_kib":1,"extra":0}',
    ],
    ids=[
        "empty",
        "malformed",
        "truncated",
        "two-documents",
        "null",
        "array",
        "bool",
        "integer",
        "duplicate-root",
        "duplicate-nested",
        "nan",
        "infinity",
        "result-type",
        "extra-key",
    ],
)
def test_invalid_output_never_returns(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], wire: str
) -> None:
    with pytest.raises(ExecutionRejected, match="^INVALID_OUTPUT$"):
        supervise(f"process.stdout.write({json.dumps(wire)});")


@WINDOWS
@pytest.mark.parametrize("peak", [0, -1, MEMORY // 1024 + 1, True, 1.0])
def test_invalid_reported_memory_rejected(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], peak: object
) -> None:
    with pytest.raises(ExecutionRejected, match="^MEMORY_LIMIT$"):
        wire = json.dumps({"result": {}, "peak_rss_kib": peak})
        supervise(f"process.stdout.write({json.dumps(wire)});")


@WINDOWS
@pytest.mark.parametrize("partial", [False, True])
def test_unexpected_exit_discards_even_complete_output(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], partial: bool
) -> None:
    wire = VALID if not partial else VALID[:-1]
    with pytest.raises(ExecutionRejected, match="^EXECUTION_FAILED$"):
        supervise(f"process.stdout.write({json.dumps(wire)}, () => process.exit(7));")


@WINDOWS
def test_deadline_discards_complete_output_and_kills_root(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]]
) -> None:
    started = time.perf_counter()
    with pytest.raises(ExecutionRejected, match="^DEADLINE$"):
        supervise(f"process.stdout.write({json.dumps(VALID)}); setInterval(() => {{}}, 100);")
    assert time.perf_counter() - started < DEADLINE + 3


@WINDOWS
def test_inflight_cancellation_discards_output(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]]
) -> None:
    cancel = threading.Event()
    timer = threading.Timer(0.4, cancel.set)
    timer.start()
    started = time.perf_counter()
    try:
        with pytest.raises(ExecutionRejected, match="^CANCELLED$"):
            supervise(
                f"process.stdout.write({json.dumps(VALID)}); setInterval(() => {{}}, 100);",
                cancel=cancel,
            )
    finally:
        timer.cancel()
        timer.join()
    assert time.perf_counter() - started < 3


@WINDOWS
@pytest.mark.parametrize("extra", [0, 1])
def test_output_limit_exact_and_one_over(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], extra: int
) -> None:
    prefix = '{"result":{"padding":"'
    suffix = '"},"peak_rss_kib":1}'
    padding = MAX_OUTPUT - len(prefix) - len(suffix) + extra
    code = f"""
import {{ once }} from 'node:events';
async function write(value) {{
  if (!process.stdout.write(value)) await once(process.stdout,'drain');
}}
await write({json.dumps(prefix)});
const block = 'x'.repeat(65536);
for (let left={padding}; left>0; left-=65536) await write(block.slice(0, Math.min(left,65536)));
await write({json.dumps(suffix)});
"""
    if extra:
        with pytest.raises(ExecutionRejected, match="^OUTPUT_LIMIT$"):
            supervise(code)
    else:
        payload, metrics = supervise(code)
        assert len(payload["result"]["padding"]) == padding
        assert metrics["output_bytes"] == MAX_OUTPUT


@WINDOWS
@pytest.mark.parametrize("extra", [0, 1])
def test_diagnostic_limit_exact_and_one_over(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], extra: int
) -> None:
    diagnostic = '{"peak_rss_kib":1}'
    diagnostic += " " * (8192 - len(diagnostic) + extra)
    code = (
        f"process.stderr.write({json.dumps(diagnostic)});process.stdout.write({json.dumps(VALID)});"
    )
    if extra:
        with pytest.raises(ExecutionRejected, match="^OUTPUT_LIMIT$"):
            supervise(code)
    else:
        payload, _ = supervise(code)
        assert payload["result"] == {}


@WINDOWS
def test_actual_committed_memory_exhaustion_returns_no_result(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]]
) -> None:
    # Retain/touch buffers so this attempts more than the fixed kernel cap.
    code = f"""
const held=[];
for (let n=0;n<20;n++) held.push(Buffer.alloc(16*1024*1024, 0x31));
process.stdout.write({json.dumps(VALID)});
"""
    with pytest.raises(ExecutionRejected, match="^(EXECUTION_FAILED|MEMORY_LIMIT|OUTPUT_LIMIT)$"):
        supervise(code)
    assert children[-1].returncode != 0


@WINDOWS
@pytest.mark.parametrize("operation", ["spawn", "file", "worker"])
def test_node_capability_denials(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]], operation: str
) -> None:
    expressions = {
        "spawn": (
            "(await import('node:child_process')).spawn(process.execPath, ['-e','process.exit(0)'])"
        ),
        "file": "await (await import('node:fs/promises')).readFile('not-permitted-synthetic.txt')",
        "worker": (
            "new (await import('node:worker_threads')).Worker("
            "'setInterval(()=>{},100)',{eval:true})"
        ),
    }
    code = f"""
let denied = null;
try {{ {expressions[operation]}; }} catch(error) {{ denied=error.code; }}
process.stdout.write(JSON.stringify({{result:{{denied}},peak_rss_kib:1}}));
"""
    payload, _ = supervise(code)
    assert payload["result"]["denied"] == "ERR_ACCESS_DENIED"


@WINDOWS
def test_no_network_gate_with_loopback_only(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]]
) -> None:
    received: list[bytes] = []
    stopped = threading.Event()
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(0.1)
    port = server.getsockname()[1]

    def listen() -> None:
        while not stopped.is_set():
            try:
                connection, _ = server.accept()
            except TimeoutError:
                continue
            with connection:
                connection.settimeout(1)
                received.append(connection.recv(64))
            return

    listener = threading.Thread(target=listen)
    listener.start()
    try:
        code = f"""
import net from 'node:net';
const connected=await new Promise(resolve=>{{
  const socket=net.createConnection({{host:'127.0.0.1',port:{port}}});
  socket.setTimeout(1000,()=>{{socket.destroy();resolve(false);}});
  socket.on('error',()=>resolve(false));
  socket.on('connect',()=>socket.end('FP6_SYNTHETIC_PROBE',()=>resolve(true)));
}});
process.stdout.write(JSON.stringify({{result:{{connected}},peak_rss_kib:1}}));
"""
        payload, _ = supervise(code)
        print(f"network_connected={payload['result']['connected']} received_count={len(received)}")
        assert payload["result"]["connected"] is False, "NO_NETWORK_GATE_FAILED"
        assert not received, "CHILD_TRANSMITTED_SYNTHETIC_SENTINEL"
    finally:
        stopped.set()
        listener.join(timeout=2)
        server.close()
        assert not listener.is_alive()


@WINDOWS
def test_blocked_stdin_writer_is_cleaned_up(
    supervise: Callable[..., Any], children: list[subprocess.Popen[bytes]]
) -> None:
    started = time.perf_counter()
    with pytest.raises(ExecutionRejected, match="^DEADLINE$"):
        supervise("setInterval(() => {}, 100);", raw=b" " * MAX_BODY, read_input=False)
    assert time.perf_counter() - started < DEADLINE + 3


@WINDOWS
def test_job_kills_inherited_descendant(tmp_path: Path) -> None:
    # Deliberately separate from the Node permission boundary: this exercises
    # actual kernel job inheritance and close, without granting Node spawning.
    from ctypes import wintypes

    script = tmp_path / "synthetic-descendant.py"
    script.write_text(
        "import subprocess,sys,time\n"
        "sys.stdin.buffer.read(1)\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])\n"
        "print(p.pid,flush=True)\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    process = subprocess.Popen(
        [sys.executable, str(script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    job = None
    descendant = None
    try:
        job = _windows_job(process)
        assert process.stdin and process.stdout
        stdout = process.stdout
        process.stdin.write(b"x")
        process.stdin.flush()
        # Read in a thread with a bounded parent wait; no unbounded readline.
        pids: list[bytes] = []
        reader = threading.Thread(target=lambda: pids.append(stdout.readline()), daemon=True)
        reader.start()
        reader.join(timeout=3)
        assert not reader.is_alive() and pids
        pid = int(pids[0])
        descendant = kernel.OpenProcess(0x00100000, False, pid)
        assert descendant
        assert kernel.WaitForSingleObject(descendant, 0) == 258  # still alive
        job[0].CloseHandle(job[1])
        job = None
        process.wait(timeout=3)
        assert kernel.WaitForSingleObject(descendant, 3000) == 0
        print(f"root_pid={process.pid} descendant_pid={pid} both_terminated=true")
    finally:
        if job:
            job[0].CloseHandle(job[1])
        if process.poll() is None:
            process.kill()
        process.wait(timeout=3)
        if descendant:
            kernel.CloseHandle(descendant)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe:
                pipe.close()
