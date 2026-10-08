"""Sandbox executor abstract base protocol, errors, and memory telemetry."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Any

from harness.kernel.context import ServiceKey


class SandboxError(Exception):
    """Raised when sandbox execution fails."""

    def __init__(self, executor: str, reason: str) -> None:
        self.executor = executor
        self.reason = reason
        super().__init__(f"Sandbox error ({executor}): {reason}")


class SandboxExecutor(ABC):
    """Abstract sandbox executor interface.

    All executors expose the same ``execute`` method so the plugin system
    can swap isolation strategies transparently.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Executor name for logging."""

    @abstractmethod
    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a method on the sandboxed plugin.

        Args:
            method: Name of the method/function to call.
            params: Parameters to pass to the method.
            timeout: Maximum execution time in seconds.

        Returns:
            Dict with ``status`` ("ok" or "error") and ``result`` or ``error``.
        """

    @abstractmethod
    async def start(self) -> None:
        """Start the sandbox environment."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the sandbox and clean up resources."""

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the sandbox is currently active."""


def _get_process_rss_mb(pid: int) -> float | None:
    """Sample RSS memory usage of a process in megabytes across operating systems."""
    try:
        import psutil

        return psutil.Process(pid).memory_info().rss / (1024 * 1024)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            process_query_information = 0x0400
            process_vm_read = 0x0010
            handle = ctypes.windll.kernel32.OpenProcess(
                process_query_information | process_vm_read, False, pid
            )
            if not handle:
                return None
            try:
                counters = _PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
                success = ctypes.windll.psapi.GetProcessMemoryInfo(
                    handle, ctypes.byref(counters), counters.cb
                )
                if success:
                    return counters.WorkingSetSize / (1024 * 1024)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return None
    elif sys.platform.startswith("linux"):
        try:
            with open(f"/proc/{pid}/statm", "r") as f:
                parts = f.read().split()
                if len(parts) >= 2:
                    pages = int(parts[1])
                    import resource

                    page_size = resource.getpagesize()
                    return (pages * page_size) / (1024 * 1024)
        except Exception:
            return None
    return None


SANDBOX_FACTORY_KEY: ServiceKey[Any] = ServiceKey("plugins.sandbox_factory")

__all__ = [
    "SANDBOX_FACTORY_KEY",
    "SandboxError",
    "SandboxExecutor",
    "_get_process_rss_mb",
]
