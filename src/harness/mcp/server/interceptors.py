"""Middleware interceptors and onion pipeline for MCP requests."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from harness.mcp.server.context import MCPRequestContext

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class MCPInterceptor(ABC):
    """Abstract middleware interceptor for MCP request pipeline."""

    @abstractmethod
    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Wrap, inspect, or modify MCP request execution."""


class MCPTelemetryInterceptor(MCPInterceptor):
    """Emits telemetry events for MCP requests and responses when event_bus is present."""

    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if ctx.event_bus:
            from harness.events.types import EventType, HarnessEvent

            req_event = HarnessEvent(
                event_type=EventType.CUSTOM,
                source="mcp.server",
                payload={"method": ctx.method, "id": ctx.request_id, "stage": "request"},
            )
            try:
                await ctx.event_bus.emit(req_event)
            except Exception:
                pass

        resp = await next_handler(ctx)

        if ctx.event_bus:
            from harness.events.types import EventType, HarnessEvent

            is_error = "error" in resp
            res_event = HarnessEvent(
                event_type=EventType.CUSTOM,
                source="mcp.server",
                payload={
                    "method": ctx.method,
                    "id": ctx.request_id,
                    "stage": "error" if is_error else "response",
                    "error": resp.get("error") if is_error else None,
                },
            )
            try:
                await ctx.event_bus.emit(res_event)
            except Exception:
                pass

        return resp


class MCPAccessControlInterceptor(MCPInterceptor):
    """Enforces allowed methods or client origin authorization policies."""

    def __init__(self, allowed_methods: set[str] | None = None) -> None:
        self.allowed_methods = allowed_methods

    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if self.allowed_methods is not None and ctx.method not in self.allowed_methods:
            return ctx.codec.encode_error(
                ctx.request_id,
                code=-32001,
                message=f"Access denied: method '{ctx.method}' is not permitted by policy",
            )
        return await next_handler(ctx)


class MCPInterceptorPipeline:
    """Composes interceptors into a single onion execution chain for MCP requests."""

    def __init__(self, interceptors: list[MCPInterceptor] | None = None) -> None:
        self._interceptors: list[MCPInterceptor] = list(interceptors or [])

    def add_interceptor(self, interceptor: MCPInterceptor) -> None:
        """Append an interceptor to the end of the pipeline."""
        self._interceptors.append(interceptor)

    async def execute(
        self,
        ctx: MCPRequestContext,
        terminal_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Execute request context through all interceptors before calling terminal handler."""
        if not self._interceptors:
            return await terminal_handler(ctx)

        async def _dispatch(idx: int, current_ctx: MCPRequestContext) -> dict[str, Any]:
            if idx >= len(self._interceptors):
                return await terminal_handler(current_ctx)

            interceptor = self._interceptors[idx]

            async def _next(next_ctx: MCPRequestContext) -> dict[str, Any]:
                return await _dispatch(idx + 1, next_ctx)

            return await interceptor.intercept(current_ctx, _next)

        return await _dispatch(0, ctx)


__all__ = [
    "MCPAccessControlInterceptor",
    "MCPInterceptor",
    "MCPInterceptorPipeline",
    "MCPTelemetryInterceptor",
]
