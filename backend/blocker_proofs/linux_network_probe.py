"""Executable x86-64 Linux seccomp building-block acceptance, NOT a sandbox.

Only the short-lived child installs its own kernel filter. No host firewall,
namespaces, cgroups, external packet, database or application behavior changes.
The deny filter is deliberately NOT the final Node syscall allowlist.
"""

import ctypes
import errno
import json
import os
import platform
import socket
import stat
import subprocess
import sys
import time


class Instruction(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(Instruction))]


def child() -> None:
    # Close every non-stdio descriptor, even one accidentally made inheritable.
    for value in os.listdir("/proc/self/fd"):
        fd = int(value)
        if fd > 2:
            try:
                os.close(fd)
            except OSError:
                pass
    if not all(stat.S_ISFIFO(os.fstat(fd).st_mode) for fd in (0, 1, 2)):
        raise SystemExit("STDIO_NOT_ANONYMOUS_PIPES")
    denied = [
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        288,
        299,
        307,
        425,
        426,
        427,
        321,
        101,
        272,
        308,
        165,
    ]
    # Audit architecture AND reject the x32 alternate ABI before syscall numbers.
    code = [
        Instruction(0x20, 0, 0, 4),
        Instruction(0x15, 1, 0, 0xC000003E),
        Instruction(0x06, 0, 0, 0x80000000),
        Instruction(0x20, 0, 0, 0),
        Instruction(0x45, 0, 1, 0x40000000),
        Instruction(0x06, 0, 0, 0x80000000),
    ]
    for number in denied:
        code.extend(
            (Instruction(0x15, 0, 1, number), Instruction(0x06, 0, 0, 0x00050000 | errno.EPERM))
        )
    code.append(Instruction(0x06, 0, 0, 0x7FFF0000))
    array = (Instruction * len(code))(*code)
    program = Program(len(code), array)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise SystemExit("NO_NEW_PRIVS_UNAVAILABLE")
    if libc.prctl(22, 2, ctypes.addressof(program), 0, 0) != 0:  # PR_SET_SECCOMP
        raise SystemExit("SECCOMP_UNAVAILABLE")
    cases: list[dict[str, object]] = []
    # No address is contacted: all transports must fail at socket creation.
    for label, family, kind in (
        ("ipv4_loopback_tcp", socket.AF_INET, socket.SOCK_STREAM),
        ("ipv6_loopback_tcp", socket.AF_INET6, socket.SOCK_STREAM),
        ("lan_tcp", socket.AF_INET, socket.SOCK_STREAM),
        ("internet_tcp", socket.AF_INET, socket.SOCK_STREAM),
        ("dns_udp", socket.AF_INET, socket.SOCK_DGRAM),
        ("dns_tcp", socket.AF_INET, socket.SOCK_STREAM),
        ("unix_broker", 1, socket.SOCK_STREAM),  # AF_UNIX in the checked Linux ABI
    ):
        try:
            with socket.socket(family, kind):
                cases.append({"id": label, "status": "FAIL"})
        except OSError as error:
            cases.append(
                {
                    "id": label,
                    "status": "PASS" if error.errno == errno.EPERM else "FAIL",
                    "errno": error.errno,
                }
            )
    try:
        a, b = socket.socketpair()
        a.close()
        b.close()
        cases.append({"id": "socketpair_broker", "status": "FAIL"})
    except OSError as error:
        cases.append(
            {
                "id": "socketpair_broker",
                "status": "PASS" if error.errno == errno.EPERM else "FAIL",
                "errno": error.errno,
            }
        )
    report = {
        "scope": "per_child_syscall_filter_only",
        "cases": cases,
        "stdio_only": True,
        "external_packets_attempted": 0,
        "full_node_boundary_proven": False,
    }
    print(json.dumps(report))
    raise SystemExit(0 if all(row["status"] == "PASS" for row in cases) else 1)


def main() -> None:
    if sys.platform != "linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        print(
            json.dumps(
                {
                    "status": "STOP",
                    "reason": "LINUX_X86_64_REQUIRED",
                    "full_node_boundary_proven": False,
                }
            )
        )
        raise SystemExit(1)
    if "--child" in sys.argv:
        child()
    else:
        # Positive control for the local receiver; never a genuine destination.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            with socket.create_connection(listener.getsockname(), timeout=1) as sender:
                sender.sendall(b"FP6_POSITIVE_CONTROL")
            connection, _ = listener.accept()
            with connection:
                assert connection.recv(64) == b"FP6_POSITIVE_CONTROL"
            os.set_inheritable(listener.fileno(), True)
            started = time.perf_counter()
            result = subprocess.run(
                [sys.executable, "-m", "blocker_proofs.linux_network_probe", "--child"],
                input=b"",
                capture_output=True,
                close_fds=True,
                timeout=5,
                check=False,
                env={"LANG": "C.UTF-8"},
            )
        print(
            json.dumps(
                {
                    "exit_code": result.returncode,
                    "seconds": round(time.perf_counter() - started, 6),
                    "positive_control": True,
                    "policy_changes_outside_child": False,
                }
            )
        )
        print(result.stdout.decode("utf-8", errors="replace"))
        if result.stderr:
            # This fixed test has no input records/tokens, but don't echo arbitrary errors.
            print(json.dumps({"diagnostics_present": True}))
        raise SystemExit(result.returncode if result.returncode >= 0 else 1)


if __name__ == "__main__":
    main()
