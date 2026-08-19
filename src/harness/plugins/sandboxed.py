"""Sandboxed plugin adapter — unified executor-backed plugin wrapper.

Binds a PluginManifest, filesystem root, and SandboxExecutor into a
full-fledged HarnessPlugin implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest
from harness.plugins.sandbox import (
    SandboxExecutor,
    SandboxExecutorFactory,
)
from harness.plugins.tool_mount import ToolMountMixin

logger = structlog.get_logger()


class SandboxedPlugin(ToolMountMixin, HarnessPlugin):
    """Canonical HarnessPlugin wrapper for manifest-based and ingested plugins.

    Delegates execution to a configured SandboxExecutor (InProcess, Subprocess, Venv)
    and exposes declared entrypoints as native tools in ToolRegistry upon enable.
    """

    def __init__(
        self,
        manifest: PluginManifest,
        root: Path,
        executor: SandboxExecutor | None = None,
    ) -> None:
        self._manifest = manifest
        self._root = Path(root).resolve()
        self._executor = executor
        self._ctx: ServiceContext | None = None
        self._invocations: int = 0
        self._errors: int = 0
        self._total_duration_ms: float = 0.0
        self._last_error: str | None = None

    @property
    def name(self) -> str:
        return self._manifest.name

    @property
    def version(self) -> str:
        return self._manifest.version

    @property
    def description(self) -> str:
        return self._manifest.description or f"Sandboxed plugin: {self.name}"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ServiceKey(name) for name in self._manifest.provides]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        declared = [ServiceKey(name) for name in self._manifest.requires]
        if self._manifest.entrypoints:
            mount_reqs = [k for k in ToolMountMixin.tool_mount_requires() if k not in declared]
            return declared + mount_reqs
        return declared

    @property
    def trusted(self) -> bool:
        return self._manifest.trusted

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    @property
    def root(self) -> Path:
        return self._root

    @property
    def executor(self) -> SandboxExecutor | None:
        return self._executor

    def _resolve_executor(self) -> SandboxExecutor | None:
        """Automatically create the appropriate SandboxExecutor if not explicitly provided."""
        if self._executor is not None:
            return self._executor

        return SandboxExecutorFactory.create(self._manifest, self._root)

    def _find_entrypoint(self) -> Path | None:
        """Find the main Python entrypoint script in the plugin root."""
        return SandboxExecutorFactory.find_entrypoint(self._manifest, self._root)

    def get_health(self) -> dict[str, Any]:
        """Return structured runtime health diagnostics for this sandboxed plugin."""
        is_running = bool(self._executor and self._executor.is_running)
        exec_name = self._executor.name if self._executor else "unresolved"
        pid = getattr(self._executor, "pid", None) if self._executor else None
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy" if is_running else "stopped",
            "isolation": self._manifest.isolation.value,
            "trusted": self._manifest.trusted,
            "executor": exec_name,
            "pid": pid,
            "last_error": self._last_error,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Return execution telemetry and performance metrics."""
        total_calls = self._invocations + self._errors
        avg_latency = (
            round(self._total_duration_ms / self._invocations, 2)
            if self._invocations > 0
            else 0.0
        )
        return {
            "name": self.name,
            "invocations": self._invocations,
            "errors": self._errors,
            "error_rate": round(self._errors / total_calls, 4) if total_calls > 0 else 0.0,
            "total_duration_ms": round(self._total_duration_ms, 2),
            "avg_latency_ms": avg_latency,
        }

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self.setup_tool_mount(ctx, self.name)
        if self._executor is None:
            self._executor = self._resolve_executor()
        for key in self.provides:
            ctx.provide(key, self, provider=self.name)

    async def on_enable(self) -> None:
        if self._executor is None:
            self._executor = self._resolve_executor()

        if self._executor:
            await self._executor.start()

        # Mount entrypoints as native tools via ToolMountMixin
        if self._manifest.entrypoints:
            from harness.services.tools import ToolSpec

            specs = [
                ToolSpec(
                    name=f"{self.name}.{ep.name}",
                    description=ep.description or f"Invoke {ep.name} on {self.name}",
                    executor=self._make_tool_executor(ep.name),
                    parameters_schema={
                        "type": "object",
                        "properties": {
                            p.name: {"type": p.type, "description": p.description}
                            for p in ep.parameters
                        },
                        "required": [p.name for p in ep.parameters if p.required],
                    },
                    provider=self.name,
                )
                for ep in self._manifest.entrypoints
            ]
            await self.mount_tools(specs)

    async def on_disable(self) -> None:
        await self.unmount_tools()

        if self._executor:
            await self._executor.stop()

    async def on_unload(self) -> None:
        if self._executor and self._executor.is_running:
            await self._executor.stop()
        self.teardown_tool_mount()
        self._ctx = None

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a method on the plugin via its sandbox executor."""
        import time

        if self._executor is None:
            self._executor = self._resolve_executor()

        if self._executor is None:
            self._errors += 1
            self._last_error = "No executor configured"
            return {"status": "error", "error": "No executor configured"}
        if not self._executor.is_running:
            self._errors += 1
            self._last_error = "Executor not running"
            return {"status": "error", "error": "Executor not running"}

        start_t = time.perf_counter()
        try:
            res = await self._executor.execute(method, params, timeout=timeout)
            duration_ms = (time.perf_counter() - start_t) * 1000.0

            if res.get("status") == "error":
                self._errors += 1
                self._last_error = res.get("error", "Unknown error")
            else:
                self._invocations += 1
                self._total_duration_ms += duration_ms

            return res
        except Exception as e:
            self._errors += 1
            self._last_error = str(e)
            raise

    def _make_tool_executor(self, method_name: str) -> Any:
        async def _exec(**kwargs: Any) -> Any:
            res = await self.call(method_name, kwargs)
            if res.get("status") == "error":
                err_msg = res.get("error", "Unknown sandbox error")
                err_code = res.get("code")
                full_msg = f"[{err_code}] {err_msg}" if err_code else err_msg
                raise RuntimeError(full_msg)
            return res.get("result")

        return _exec

    def __repr__(self) -> str:
        exec_name = self._executor.name if self._executor else "auto"
        return f"<SandboxedPlugin {self.name}@{self.version} [executor={exec_name}]>"
