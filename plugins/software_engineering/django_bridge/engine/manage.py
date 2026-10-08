"""Safe Django management command execution in guarded subprocess sandbox."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

from harness.services.django_bridge import (
    SAFE_MANAGEMENT_COMMANDS,
    DjangoManageResult,
)


async def execute_manage_command(
    project_path: str,
    command: str,
    args: list[str] | None = None,
    settings_module: str | None = None,
    timeout_sec: float = 30.0,
) -> DjangoManageResult:
    """Execute a safe Django management command in a guarded subprocess."""
    cmd_clean = command.strip().lower()
    if cmd_clean not in SAFE_MANAGEMENT_COMMANDS:
        return DjangoManageResult(
            command=command,
            args=tuple(args or []),
            exit_code=1,
            stdout="",
            stderr=f"Command '{command}' is not permitted in sandboxed execution. Safe commands: {sorted(SAFE_MANAGEMENT_COMMANDS)}",
            duration_ms=0.0,
            success=False,
        )

    root = Path(project_path).resolve()
    manage_py = root / "manage.py"

    if not manage_py.exists():
        for sub in root.iterdir():
            if sub.is_dir() and (sub / "manage.py").exists():
                manage_py = sub / "manage.py"
                break

    if not manage_py.exists():
        return DjangoManageResult(
            command=command,
            args=tuple(args or []),
            exit_code=1,
            stdout="",
            stderr=f"manage.py not found in {project_path}",
            duration_ms=0.0,
            success=False,
        )

    cmd_args = [sys.executable, str(manage_py), cmd_clean]
    if args:
        cmd_args.extend([str(a) for a in args])

    env = dict(os.environ)
    if settings_module:
        env["DJANGO_SETTINGS_MODULE"] = settings_module

    start_time = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(manage_py.parent),
            env=env,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_sec,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")
        code = proc.returncode if proc.returncode is not None else 0

        return DjangoManageResult(
            command=command,
            args=tuple(args or []),
            exit_code=code,
            stdout=stdout_str,
            stderr=stderr_str,
            duration_ms=duration_ms,
            success=(code == 0),
        )
    except asyncio.TimeoutError:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return DjangoManageResult(
            command=command,
            args=tuple(args or []),
            exit_code=124,
            stdout="",
            stderr=f"Command execution timed out after {timeout_sec} seconds",
            duration_ms=duration_ms,
            success=False,
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return DjangoManageResult(
            command=command,
            args=tuple(args or []),
            exit_code=1,
            stdout="",
            stderr=f"Execution error: {e}",
            duration_ms=duration_ms,
            success=False,
        )
