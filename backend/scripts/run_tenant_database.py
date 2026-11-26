"""Fresh fictional cluster + independent in-memory credentials; no .env or secrets artifact.

Default: Docker PostgreSQL 17.12 (CI). Native local alternative:
  uv run --frozen python -m scripts.run_tenant_database --postgres-bin <17/bin>
Native database/log evidence stays under .local; the bootstrap pwfile is removed.
"""

import argparse
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

from experiments.tenant_db import DATABASE, LOGIN_ENV, MARKER, ROOT


def command(args: list[str], env: dict[str, str]) -> None:
    # A background native server must not inherit a captured pipe and keep its
    # parent's communicate() waiting for EOF on Windows. No setup output is needed.
    result = subprocess.run(
        args,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )
    if result.returncode:
        # Do not expose subprocess diagnostics from password-bearing setup.
        raise RuntimeError("Disposable PostgreSQL setup/cleanup failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-bin", type=Path)
    args = parser.parse_args()
    env = {key: value for key, value in os.environ.items() if key != "FP6_TEST_PASSWORD"}
    for variable in LOGIN_ENV.values():
        env[variable] = secrets.token_hex(32)
    if len({env[key] for key in LOGIN_ENV.values()}) != 4:
        raise RuntimeError("Independent synthetic credential generation failed")
    env.update(FP6_SYNTHETIC_ONLY=MARKER)
    port = env.setdefault("FP6_TEST_PORT", "55433")
    env["PGPASSWORD"] = env["FP6_BOOTSTRAP_PASSWORD"]
    container = "fp6c02-disposable-" + uuid4().hex
    native: Path | None = args.postgres_bin
    data: Path | None = None
    started = False
    try:
        if native is not None:
            evidence = ROOT.parent / ".local" / container
            evidence.mkdir(parents=True, exist_ok=False)
            data = evidence / "pgdata"
            password_file = evidence / "bootstrap-password"
            try:
                password_file.write_text(env["FP6_BOOTSTRAP_PASSWORD"], encoding="ascii")
                command(
                    [
                        str(native / "initdb.exe"),
                        "-D",
                        str(data),
                        "-U",
                        "fp6_bootstrap",
                        "-A",
                        "scram-sha-256",
                        "--pwfile",
                        str(password_file),
                        "--encoding=UTF8",
                        "--locale=C",
                    ],
                    env,
                )
            finally:
                password_file.unlink(missing_ok=True)
            with (data / "postgresql.conf").open("a", encoding="utf-8") as config:
                config.write(
                    f"\nlisten_addresses='127.0.0.1'\nport={int(port)}\n"
                    "log_statement='none'\nlog_min_error_statement='panic'\n"
                    "log_parameter_max_length_on_error=0\n"
                )
            command(
                [
                    str(native / "pg_ctl.exe"),
                    "-D",
                    str(data),
                    "-l",
                    str(evidence / "postgres.log"),
                    "start",
                    "-w",
                ],
                env,
            )
            started = True
            command(
                [
                    str(native / "createdb.exe"),
                    "-h",
                    "127.0.0.1",
                    "-p",
                    port,
                    "-U",
                    "fp6_bootstrap",
                    DATABASE,
                ],
                env,
            )
        else:
            env.update(
                POSTGRES_USER="fp6_bootstrap",
                POSTGRES_DB=DATABASE,
                POSTGRES_PASSWORD=env["FP6_BOOTSTRAP_PASSWORD"],
            )
            command(
                [
                    "docker",
                    "run",
                    "--name",
                    container,
                    "--detach",
                    "--publish",
                    f"127.0.0.1:{int(port)}:5432",
                    "--env",
                    "POSTGRES_USER",
                    "--env",
                    "POSTGRES_DB",
                    "--env",
                    "POSTGRES_PASSWORD",
                    "postgres:17.12-bookworm",
                    "-c",
                    "log_statement=none",
                    "-c",
                    "log_min_error_statement=panic",
                    "-c",
                    "log_parameter_max_length_on_error=0",
                ],
                env,
            )
            started = True
            for _ in range(30):
                ready = subprocess.run(
                    [
                        "docker",
                        "exec",
                        container,
                        "pg_isready",
                        "-h",
                        "127.0.0.1",
                        "-U",
                        "fp6_bootstrap",
                        "-d",
                        DATABASE,
                    ],
                    env=env,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
                if ready.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Disposable PostgreSQL did not become ready")
        # Redact even unexpected child diagnostics before releasing them to CI logs.
        result = subprocess.run(
            [sys.executable, "-m", "scripts.check_tenant_database"],
            cwd=ROOT,
            env={
                key: value
                for key, value in env.items()
                if key not in ("PGPASSWORD", "POSTGRES_PASSWORD")
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=600,
        )
        output = result.stdout
        for variable in LOGIN_ENV.values():
            output = output.replace(env[variable], "[REDACTED]")
        print(output, end="", flush=True)
        if result.returncode:
            raise RuntimeError("Synthetic tenant regression failed; see redacted output")
    finally:
        if started:
            if native is not None and data is not None:
                command([str(native / "pg_ctl.exe"), "-D", str(data), "stop", "-w"], env)
            else:
                command(["docker", "rm", "--force", "--volumes", container], env)


if __name__ == "__main__":
    main()
