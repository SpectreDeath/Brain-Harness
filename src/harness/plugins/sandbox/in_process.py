"""In-process plugin execution for trusted, built-in components (Rule 5)."""

from __future__ import annotations

import asyncio
from typing import Any

from harness.plugins.sandbox.base import SandboxExecutor


class InProcessExecutor(SandboxExecutor):
    """Execute plugin code directly in the harness process.

    Only for trusted, built-in plugins (Rule 5). No isolation is provided.
    """

    def __init__(self, module: Any) -> None:
        """Initialize with a Python module or object.

        Args:
            module: The module or object containing callable methods.
        """
        self._module = module
        self._running = False

    @property
    def name(self) -> str:
        return "in_process"

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if not self._running:
            return {"status": "error", "error": "Executor not running"}

        func = getattr(self._module, method, None)
        if func is None:
            return {"status": "error", "error": f"Method not found: {method}"}

        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(**(params or {})), timeout=timeout)
            else:
                result = func(**(params or {}))

            return {"status": "ok", "result": result}
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


__all__ = ["InProcessExecutor"]
