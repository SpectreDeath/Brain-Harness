"""Subprocess execution via JSON-RPC with kernel OOM resource constraints."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
from typing import Any

import structlog

from harness.plugins.sandbox.base import (
    SandboxError,
    SandboxExecutor,
    _get_process_rss_mb,
)
from harness.plugins.transport import StdioJsonRpcTransport

logger = structlog.get_logger()


class SubprocessExecutor(SandboxExecutor):
    """Execute plugin code in a separate Python subprocess via JSON-RPC over stdin/stdout."""

    def __init__(
        self,
        script_path: Path,
        *,
        python: str | None = None,
        env: dict[str, str] | None = None,
        memory_limit_mb: float = 512.0,
        watchdog_interval: float = 2.0,
        network_disabled: bool = False,
    ) -> None:
        self._script_path = script_path
        self._python = python or getattr(sys, "_base_executable", sys.executable)
        self._env = env
        self._memory_limit_mb = memory_limit_mb
        self._watchdog_interval = watchdog_interval
        self._network_disabled = network_disabled
        self._transport: StdioJsonRpcTransport | None = None
        self._watchdog_task: asyncio.Task[None] | None = None
        self._memory_exceeded: bool = False
        self._win32_job_handle: Any = None
        self._cgroup_path: Path | None = None

    @property
    def name(self) -> str:
        return "subprocess"

    @property
    def is_running(self) -> bool:
        return self._transport is not None and self._transport.is_running

    @property
    def transport(self) -> StdioJsonRpcTransport | None:
        """The underlying StdioJsonRpcTransport instance."""
        return self._transport

    def _resolve_runner_path(self) -> Path:
        """Resolve bridge_runner.py path across workspace layout variations."""
        runner = Path(__file__).resolve().parent.parent / "bridge_runner.py"
        if not runner.exists():
            runner = Path(__file__).resolve().parent / "bridge_runner.py"
        return runner

    async def _memory_watchdog(self) -> None:
        """Background watchdog sampling RSS memory and stopping child if limit exceeded."""
        try:
            while self.is_running and self._transport:
                pid = getattr(self._transport, "pid", None)
                if pid:
                    rss = _get_process_rss_mb(pid)
                    if rss is not None and rss > self._memory_limit_mb:
                        logger.error(
                            "Subprocess exceeded memory limit; terminating",
                            script=str(self._script_path),
                            pid=pid,
                            rss_mb=rss,
                            limit_mb=self._memory_limit_mb,
                        )
                        self._memory_exceeded = True
                        if self._transport:
                            await self._transport.stop()
                            self._transport = None
                        break
                await asyncio.sleep(self._watchdog_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Memory watchdog error", error=str(e))

    def _apply_win32_job_limits(self, pid: int, limit_mb: float) -> None:
        """Assign Windows Job Object with process memory limit for instant kernel OOM enforcement."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("ReadOperationCount", ctypes.c_uint64),
                    ("WriteOperationCount", ctypes.c_uint64),
                    ("OtherOperationCount", ctypes.c_uint64),
                    ("ReadTransferCount", ctypes.c_uint64),
                    ("WriteTransferCount", ctypes.c_uint64),
                    ("OtherTransferCount", ctypes.c_uint64),
                ]

            class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                    ("IoInfo", IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
            JobObjectExtendedLimitInformation = 9
            PROCESS_SET_QUOTA = 0x0100
            PROCESS_TERMINATE = 0x0001

            job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            if not job:
                return

            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY
            info.ProcessMemoryLimit = int(limit_mb * 1024 * 1024)

            success = ctypes.windll.kernel32.SetInformationJobObject(
                job,
                JobObjectExtendedLimitInformation,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
            if not success:
                return

            proc_handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid
            )
            if proc_handle:
                ctypes.windll.kernel32.AssignProcessToJobObject(job, proc_handle)
                ctypes.windll.kernel32.CloseHandle(proc_handle)
                self._win32_job_handle = job
                logger.debug(
                    "Win32 Job Object memory limit applied", pid=pid, limit_mb=limit_mb
                )
        except Exception as e:
            logger.debug("Failed applying Win32 Job Object limits", error=str(e))

    def _resolve_cgroup_path(
        self,
        pid: int,
        cgroup_root: Path = Path("/sys/fs/cgroup"),
        proc_cgroup: Path = Path("/proc/self/cgroup"),
    ) -> Path | None:
        """Detect a writable cgroup v2 slice for this process."""
        cgroup_controllers = cgroup_root / "cgroup.controllers"
        if not cgroup_controllers.exists():
            return None  # not a cgroups v2 host
        if not proc_cgroup.exists():
            return None
        try:
            # Read own slice from kernel (format: "0::/<slice_path>")
            content = proc_cgroup.read_text(encoding="utf-8").strip()
            lines = content.splitlines()
            if not lines:
                return None
            own_cgroup = lines[0].split(":")[-1]
            slice_path = cgroup_root / own_cgroup.lstrip("/")
            candidate = slice_path / f"harness_{pid}"
            candidate.mkdir(parents=False, exist_ok=True)
            return candidate
        except (PermissionError, OSError):
            return None  # fall through to RSS watchdog

    def _apply_cgroup_limits(
        self,
        pid: int,
        limit_mb: float,
        cgroup_root: Path = Path("/sys/fs/cgroup"),
        proc_cgroup: Path = Path("/proc/self/cgroup"),
    ) -> bool:
        """Apply memory.max and cgroup.procs for kernel-level OOM enforcement on Linux."""
        cgroup_dir = self._resolve_cgroup_path(
            pid, cgroup_root=cgroup_root, proc_cgroup=proc_cgroup
        )
        if not cgroup_dir:
            return False
        try:
            mem_bytes = int(limit_mb * 1024 * 1024)
            (cgroup_dir / "memory.max").write_text(str(mem_bytes), encoding="utf-8")
            (cgroup_dir / "cgroup.procs").write_text(str(pid), encoding="utf-8")
            self._cgroup_path = cgroup_dir
            logger.debug(
                "Linux cgroup v2 memory limit applied",
                pid=pid,
                cgroup=str(cgroup_dir),
                limit_mb=limit_mb,
            )
            return True
        except (PermissionError, OSError) as e:
            logger.debug("Failed applying cgroup v2 memory limit", error=str(e))
            return False

    def _cleanup_cgroup(self) -> None:
        """Cleanly remove the cgroup directory if one was created."""
        if self._cgroup_path is not None:
            try:
                if self._cgroup_path.exists():
                    self._cgroup_path.rmdir()
            except OSError:
                pass
            self._cgroup_path = None

    async def start(self) -> None:
        runner_path = self._resolve_runner_path()
        child_env = dict(self._env) if self._env else os.environ.copy()
        if hasattr(sys, "prefix") and hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
            child_env.setdefault("VIRTUAL_ENV", sys.prefix)
        if self._network_disabled:
            child_env["HARNESS_NO_NETWORK"] = "1"
        self._transport = StdioJsonRpcTransport(
            self._python,
            [str(runner_path), str(self._script_path)],
            env=child_env,
        )
        self._memory_exceeded = False
        await self._transport.start(negotiate=True)

        if self._memory_limit_mb is not None and self._memory_limit_mb > 0:
            if self._transport and self._transport.pid:
                if sys.platform == "win32":
                    self._apply_win32_job_limits(self._transport.pid, self._memory_limit_mb)
                elif sys.platform.startswith("linux"):
                    self._apply_cgroup_limits(self._transport.pid, self._memory_limit_mb)
            self._watchdog_task = asyncio.create_task(self._memory_watchdog())

        logger.info(
            "Subprocess sandbox started",
            script=str(self._script_path),
            pid=self._transport.pid,
            memory_limit_mb=self._memory_limit_mb,
            network_disabled=self._network_disabled,
        )

    async def stop(self) -> None:
        """Terminate the subprocess."""
        if self._watchdog_task and not self._watchdog_task.done():
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None

        if self._win32_job_handle:
            try:
                import ctypes

                ctypes.windll.kernel32.CloseHandle(self._win32_job_handle)
            except Exception:
                pass
            self._win32_job_handle = None

        self._cleanup_cgroup()

        if self._transport:
            await self._transport.stop()
            self._transport = None
        await asyncio.sleep(0.01)

        logger.info("Subprocess sandbox stopped", script=str(self._script_path))

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if self._memory_exceeded or (self._win32_job_handle is not None and not self.is_running):
            raise SandboxError(
                "subprocess",
                f"Process exceeded memory limit of {self._memory_limit_mb:.0f} MB",
            )

        if not self.is_running or self._transport is None:
            return {"status": "error", "error": "Subprocess not running"}

        try:
            resp = await self._transport.call(method, params, timeout=timeout)
            if self._memory_exceeded:
                raise SandboxError(
                    "subprocess",
                    f"Process exceeded memory limit of {self._memory_limit_mb:.0f} MB",
                )
            if "error" in resp:
                return {"status": "error", "error": resp["error"]}
            return {"status": "ok", "result": resp.get("result")}
        except Exception as e:
            if self._memory_exceeded:
                raise SandboxError(
                    "subprocess",
                    f"Process exceeded memory limit of {self._memory_limit_mb:.0f} MB",
                )
            return {"status": "error", "error": str(e)}


__all__ = ["SubprocessExecutor"]
