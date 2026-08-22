"""Sandboxed plugin adapter — unified executor-backed plugin wrapper.

Binds a PluginManifest, filesystem root, and SandboxExecutor into a
full-fledged HarnessPlugin implementation with structured invocation results,
categorized error handling, and runtime telemetry.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
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


@dataclass(slots=True)
class PluginCallResult:
    """Structured result from a plugin method invocation."""

    status: str  # "ok" or "error"
    result: Any = None
    error: str | None = None
    error_code: str | None = None  # "TIMEOUT", "NOT_FOUND", "SANDBOX_NOT_RUNNING", "NO_EXECUTOR", "EXECUTION_ERROR"
    latency_ms: float = 0.0
    method: str = ""
    plugin: str = ""
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    def to_dict(self) -> dict[str, Any]:
        """Backward-compatible dictionary conversion."""
        if self.status == "ok":
            return {"status": "ok", "result": self.result}
        d: dict[str, Any] = {"status": "error", "error": self.error or "Unknown error"}
        if self.error_code:
            d["code"] = self.error_code
        return d


class SandboxedPlugin(ToolMountMixin, HarnessPlugin):
    """Canonical HarnessPlugin wrapper for manifest-based and ingested plugins.

    Delegates execution to a configured SandboxExecutor (InProcess, Subprocess, Venv, Container)
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
        declared: list[ServiceKey[Any]] = [ServiceKey(name) for name in self._manifest.requires]
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

    async def invoke_typed(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
        correlation_id: str | None = None,
    ) -> PluginCallResult:
        """Execute a method on the plugin returning a strongly-typed PluginCallResult."""
        cid = correlation_id or uuid.uuid4().hex[:12]

        if self._executor is None:
            self._executor = self._resolve_executor()

        if self._executor is None:
            self._errors += 1
            self._last_error = "No executor configured"
            self._emit_failure_event(method, "No executor configured", "NO_EXECUTOR", cid)
            return PluginCallResult(
                status="error",
                error="No executor configured",
                error_code="NO_EXECUTOR",
                method=method,
                plugin=self.name,
                correlation_id=cid,
            )

        if not self._executor.is_running:
            self._errors += 1
            self._last_error = "Executor not running"
            self._emit_failure_event(method, "Executor not running", "SANDBOX_NOT_RUNNING", cid)
            return PluginCallResult(
                status="error",
                error="Executor not running",
                error_code="SANDBOX_NOT_RUNNING",
                method=method,
                plugin=self.name,
                correlation_id=cid,
            )

        start_t = time.perf_counter()
        try:
            res = await self._executor.execute(method, params, timeout=timeout)
            duration_ms = (time.perf_counter() - start_t) * 1000.0

            if res.get("status") == "error":
                err_msg = res.get("error", "Unknown error")
                err_code = "TIMEOUT" if "Timeout" in err_msg else "EXECUTION_ERROR"
                if "not found" in err_msg.lower():
                    err_code = "NOT_FOUND"

                self._errors += 1
                self._last_error = err_msg
                self._emit_failure_event(method, err_msg, err_code, cid)
                return PluginCallResult(
                    status="error",
                    error=err_msg,
                    error_code=err_code,
                    latency_ms=duration_ms,
                    method=method,
                    plugin=self.name,
                    correlation_id=cid,
                )

            self._invocations += 1
            self._total_duration_ms += duration_ms
            return PluginCallResult(
                status="ok",
                result=res.get("result"),
                latency_ms=duration_ms,
                method=method,
                plugin=self.name,
                correlation_id=cid,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            self._errors += 1
            self._last_error = str(e)
            self._emit_failure_event(method, str(e), "SANDBOX_EXCEPTION", cid)
            raise

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a method on the plugin via its sandbox executor (dict interface)."""
        call_res = await self.invoke_typed(method, params, timeout=timeout)
        return call_res.to_dict()

    def _emit_failure_event(
        self, method: str, error: str, error_code: str, correlation_id: str
    ) -> None:
        """Emit a structured failure event to the harness EventBus if available."""
        if not self._ctx:
            return
        bus_key: ServiceKey[Any] = ServiceKey("events.bus")
        if self._ctx.has(bus_key):
            try:
                from harness.events.types import EventType, HarnessEvent

                bus = self._ctx.require(bus_key)
                evt = HarnessEvent(
                    event_type=EventType.PLUGIN_ERROR,
                    source=self.name,
                    payload={
                        "plugin": self.name,
                        "method": method,
                        "error": error,
                        "error_code": error_code,
                        "correlation_id": correlation_id,
                    },
                )
                bus.fire(evt)
            except Exception:
                pass

    def _make_tool_executor(self, method_name: str) -> Any:
        async def _exec(**kwargs: Any) -> Any:
            res = await self.invoke_typed(method_name, kwargs)
            if res.is_error:
                err_msg = res.error or "Unknown sandbox error"
                err_code = res.error_code
                full_msg = f"[{err_code}] {err_msg}" if err_code else err_msg
                raise RuntimeError(full_msg)
            return res.result

        return _exec

    def __repr__(self) -> str:
        exec_name = self._executor.name if self._executor else "auto"
        return f"<SandboxedPlugin {self.name}@{self.version} [executor={exec_name}]>"
