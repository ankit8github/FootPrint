"""Native process-creation probe, NOT an adopted sandbox or general launcher.

No profile creation, DACL changes, firewall changes or external addresses. An
unregistered random AppContainer SID is derived in memory. Existing file ACLs
may refuse Node; that is a failed prerequisite, never an excuse to grant access.
"""

import ctypes
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from ctypes import wintypes as w
from pathlib import Path
from typing import Any
from uuid import uuid4


class Unavailable(Exception):
    """Fixed safe status for an unproven prerequisite."""


class Basic(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64),
        ("job_time", ctypes.c_int64),
        ("flags", w.DWORD),
        ("minimum", ctypes.c_size_t),
        ("maximum", ctypes.c_size_t),
        ("active", w.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority", w.DWORD),
        ("scheduling", w.DWORD),
    ]


class Extended(ctypes.Structure):
    _fields_ = [
        ("basic", Basic),
        ("io", ctypes.c_uint64 * 6),
        ("process_limit", ctypes.c_size_t),
        ("job_limit", ctypes.c_size_t),
        ("peak_process", ctypes.c_size_t),
        ("peak_job", ctypes.c_size_t),
    ]


class Startup(ctypes.Structure):
    _fields_ = [
        ("cb", w.DWORD),
        ("reserved", w.LPWSTR),
        ("desktop", w.LPWSTR),
        ("title", w.LPWSTR),
        ("x", w.DWORD),
        ("y", w.DWORD),
        ("xs", w.DWORD),
        ("ys", w.DWORD),
        ("xc", w.DWORD),
        ("yc", w.DWORD),
        ("fill", w.DWORD),
        ("flags", w.DWORD),
        ("show", w.WORD),
        ("reserved_size", w.WORD),
        ("reserved_bytes", ctypes.c_void_p),
        ("stdin", w.HANDLE),
        ("stdout", w.HANDLE),
        ("stderr", w.HANDLE),
    ]


class StartupEx(ctypes.Structure):
    _fields_ = [("startup", Startup), ("attributes", ctypes.c_void_p)]


class Process(ctypes.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]


class Capabilities(ctypes.Structure):
    _fields_ = [
        ("sid", ctypes.c_void_p),
        ("capabilities", ctypes.c_void_p),
        ("count", w.DWORD),
        ("reserved", w.DWORD),
    ]


def native_probe(port: int) -> dict[str, Any]:
    if sys.platform != "win32" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise Unavailable("UNSUPPORTED_PLATFORM")
    if not 1 <= port <= 65535:
        raise Unavailable("INVALID_LOCAL_PORT")
    import msvcrt

    node = shutil.which("node")
    if not node:
        raise Unavailable("NODE_UNAVAILABLE")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.QueryInformationJobObject.argtypes = [
        w.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        w.DWORD,
        ctypes.c_void_p,
    ]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        w.DWORD,
        w.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel.UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        w.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    kernel.CreateProcessW.argtypes = [
        w.LPCWSTR,
        w.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        w.BOOL,
        w.DWORD,
        ctypes.c_void_p,
        w.LPCWSTR,
        ctypes.POINTER(StartupEx),
        ctypes.POINTER(Process),
    ]
    kernel.ResumeThread.argtypes = [w.HANDLE]
    kernel.ResumeThread.restype = w.DWORD
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    kernel.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
    kernel.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    security.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    security.GetTokenInformation.argtypes = [
        w.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        w.DWORD,
        ctypes.POINTER(w.DWORD),
    ]
    security.FreeSid.argtypes = [ctypes.c_void_p]
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
        w.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
    sid = ctypes.c_void_p()
    token = w.HANDLE()
    process = Process()
    job = None
    attributes = None
    attributes_initialized = False
    fds: list[int] = []
    reader: threading.Thread | None = None
    raw = bytearray()
    try:
        if (
            userenv.DeriveAppContainerSidFromAppContainerName(
                "FootPrint.Probe." + uuid4().hex, ctypes.byref(sid)
            )
            != 0
        ):
            raise Unavailable("SID_DERIVATION_FAILED")
        # Both per-process and aggregate committed limits; no breakaway flag.
        limits = Extended()
        limits.basic.flags = 0x0100 | 0x0200 | 0x2000 | 0x0008
        limits.basic.active = 1
        limits.process_limit = limits.job_limit = 256 * 1024 * 1024
        job = kernel.CreateJobObjectW(None, None)
        if not job or not kernel.SetInformationJobObject(
            job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise Unavailable("JOB_CONFIGURATION_FAILED")
        in_read, in_write = os.pipe()
        out_read, out_write = os.pipe()
        fds.extend((in_read, in_write, out_read, out_write))
        for fd in (in_read, out_write):
            os.set_inheritable(fd, True)
        handles = (w.HANDLE * 2)(msvcrt.get_osfhandle(in_read), msvcrt.get_osfhandle(out_write))
        caps = Capabilities(sid, None, 0, 0)
        jobs = (w.HANDLE * 1)(job)
        child_policy = w.DWORD(1)  # PROCESS_CREATION_CHILD_PROCESS_RESTRICTED
        size = ctypes.c_size_t()
        kernel.InitializeProcThreadAttributeList(None, 4, 0, ctypes.byref(size))
        attributes = ctypes.create_string_buffer(size.value)
        if not kernel.InitializeProcThreadAttributeList(attributes, 4, 0, ctypes.byref(size)):
            raise Unavailable("ATTRIBUTE_INIT_FAILED")
        attributes_initialized = True
        for key, value in (
            (0x20009, caps),
            (0x20002, handles),
            (0x2000D, jobs),
            (0x2000E, child_policy),
        ):
            if not kernel.UpdateProcThreadAttribute(
                attributes, 0, key, ctypes.byref(value), ctypes.sizeof(value), None, None
            ):
                raise Unavailable("ATTRIBUTE_CONFIGURATION_FAILED")
        startup = StartupEx()
        startup.startup.cb = ctypes.sizeof(startup)
        startup.startup.flags = 0x00000100  # STARTF_USESTDHANDLES
        startup.startup.stdin, startup.startup.stdout = handles[0], handles[1]
        startup.startup.stderr = handles[1]
        startup.attributes = ctypes.cast(attributes, ctypes.c_void_p)
        code = f"""
const net=require('node:net');
process.stdin.resume();process.stdin.on('end',()=>{{
 const s=net.createConnection({{host:'127.0.0.1',port:{port}}});
 s.setTimeout(700,()=>{{s.destroy();process.exitCode=3;}});
 s.on('error',e=>console.log(JSON.stringify({{connected:false,code:e.code}})));
 s.on('connect',()=>s.end('FP6_APPCONTAINER_PROBE',()=>console.log('{{"connected":true}}')));
}});
"""
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline([node, "-e", code]))
        # No PATH lookup in the child, NODE_OPTIONS, proxy, token or network handle.
        environment = ctypes.create_unicode_buffer(
            "\0".join(f"{k}={os.environ[k]}" for k in ("SystemRoot", "WINDIR") if k in os.environ)
            + "\0\0"
        )
        start = time.perf_counter()
        flags = 0x00080000 | 0x00000004 | 0x00000400 | 0x08000000
        if not kernel.CreateProcessW(
            node,
            command,
            None,
            None,
            True,
            flags,
            environment,
            os.environ.get("SystemRoot", "C:\\Windows"),
            ctypes.byref(startup),
            ctypes.byref(process),
        ):
            return {
                "status": "STOP",
                "stage": "CreateProcessW",
                "winerror": ctypes.get_last_error(),
                "worker_resumed": False,
                "policy_changes": False,
            }
        if not security.OpenProcessToken(process.process, 0x0008, ctypes.byref(token)):
            raise Unavailable("TOKEN_QUERY_FAILED")
        appcontainer, returned = w.DWORD(), w.DWORD()
        capability_buffer = ctypes.create_string_buffer(4096)
        if (
            not security.GetTokenInformation(
                token, 29, ctypes.byref(appcontainer), 4, ctypes.byref(returned)
            )
            or appcontainer.value != 1
        ):
            raise Unavailable("NOT_APPCONTAINER")
        if not security.GetTokenInformation(
            token, 30, capability_buffer, 4096, ctypes.byref(returned)
        ):
            raise Unavailable("CAPABILITY_QUERY_FAILED")
        if w.DWORD.from_buffer(capability_buffer).value != 0:
            raise Unavailable("UNEXPECTED_CAPABILITY")
        observed = Extended()
        if not kernel.QueryInformationJobObject(
            job, 9, ctypes.byref(observed), ctypes.sizeof(observed), None
        ):
            raise Unavailable("JOB_QUERY_FAILED")
        if observed.job_limit != limits.job_limit or observed.basic.flags != limits.basic.flags:
            raise Unavailable("JOB_LIMIT_MISMATCH")
        os.close(in_read)
        fds.remove(in_read)
        os.close(out_write)
        fds.remove(out_write)

        def read() -> None:
            while block := os.read(out_read, 1024):
                raw.extend(block)
                if len(raw) > 8192:
                    kernel.TerminateJobObject(job, 1)
                    break

        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        if kernel.ResumeThread(process.thread) == 0xFFFFFFFF:
            raise Unavailable("RESUME_FAILED")
        os.close(in_write)
        fds.remove(in_write)
        timed_out = kernel.WaitForSingleObject(process.process, 5000) != 0
        if timed_out:
            kernel.TerminateJobObject(job, 1)
        if kernel.WaitForSingleObject(process.process, 1000) != 0:
            raise Unavailable("CLEANUP_UNPROVEN")
        reader.join(timeout=1)
        if reader.is_alive():
            raise Unavailable("PIPE_CLEANUP_UNPROVEN")
        exit_code = w.DWORD()
        if not kernel.GetExitCodeProcess(process.process, ctypes.byref(exit_code)):
            raise Unavailable("EXIT_QUERY_FAILED")
        return {
            "status": "PROBE_ONLY",
            "appcontainer": True,
            "capability_count": 0,
            "job_memory_bytes": observed.job_limit,
            "child_policy_restricted": True,
            "worker_resumed": True,
            "policy_changes": False,
            "seconds": round(time.perf_counter() - start, 6),
            "timeout": timed_out,
            "exit_code": exit_code.value,
            "output": raw.decode("utf-8", errors="replace"),
            "node_sha256": hashlib.sha256(Path(node).read_bytes()).hexdigest(),
        }
    finally:
        if job:
            kernel.TerminateJobObject(job, 1)
        if process.process:
            kernel.WaitForSingleObject(process.process, 1000)
        for handle in (process.thread, process.process, token, job):
            if handle:
                kernel.CloseHandle(handle)
        if reader:
            reader.join(timeout=1)
        for fd in fds:
            os.close(fd)
        if attributes_initialized:
            kernel.DeleteProcThreadAttributeList(attributes)
        if sid:
            security.FreeSid(sid)


def main() -> None:
    received: list[bytes] = []
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.settimeout(0.1)
        stopped = threading.Event()

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
            result = native_probe(server.getsockname()[1])
        except Unavailable as error:
            result = {"status": "STOP", "reason": str(error), "policy_changes": False}
        finally:
            stopped.set()
            listener.join(timeout=2)
        result["received_count"] = len(received)
        print(json.dumps(result))
        # Absence of a packet after a failed launch is never a passing sandbox.
        proved = result.get("worker_resumed") and result.get("exit_code") == 0
        if proved:
            try:
                child = json.loads(result["output"])
                proved = child.get("connected") is False and child.get("code") == "EACCES"
            except (ValueError, KeyError):
                proved = False
        sys.exit(0 if proved and not received else 1)


if __name__ == "__main__":
    main()
