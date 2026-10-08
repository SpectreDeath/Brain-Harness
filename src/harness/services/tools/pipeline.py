"""Tool execution pipeline implementing onion-layer middleware chaining."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from harness.services.tools.interceptors import (
    AccessControlInterceptor,
    MemoizationInterceptor,
    RateLimitInterceptor,
    SchemaValidationInterceptor,
    TelemetryInterceptor,
    TimeoutGuardInterceptor,
    ToolInterceptor,
)
from harness.services.tools.models import ToolExecutionContext


class ToolExecutionPipeline:
    """Onion-layer middleware execution pipeline for tools."""

    def __init__(self, interceptors: list[ToolInterceptor] | None = None) -> None:
        self._interceptors: list[ToolInterceptor] = (
            list(interceptors)
            if interceptors is not None
            else [
                TelemetryInterceptor(),
                AccessControlInterceptor(),
                RateLimitInterceptor(),
                MemoizationInterceptor(),
                SchemaValidationInterceptor(),
                TimeoutGuardInterceptor(),
            ]
        )

    @property
    def interceptors(self) -> list[ToolInterceptor]:
        """List of active pipeline interceptors."""
        return list(self._interceptors)

    def add_interceptor(
        self, interceptor: ToolInterceptor, position: int | None = None
    ) -> None:
        """Insert an interceptor into the execution pipeline."""
        if position is not None:
            self._interceptors.insert(position, interceptor)
        else:
            # Insert before the terminal TimeoutGuardInterceptor if present
            if self._interceptors and isinstance(
                self._interceptors[-1], TimeoutGuardInterceptor
            ):
                self._interceptors.insert(len(self._interceptors) - 1, interceptor)
            else:
                self._interceptors.append(interceptor)

    async def execute(self, ctx: ToolExecutionContext) -> dict[str, Any]:
        """Execute tool execution context through the interceptor chain."""

        async def _terminal(c: ToolExecutionContext) -> dict[str, Any]:
            guard = TimeoutGuardInterceptor()
            return await guard.intercept(c, lambda _: asyncio.sleep(0, result={"status": "ok"}))  # type: ignore[return-value]

        handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]] = _terminal
        for interceptor in reversed(self._interceptors):
            prev_handler = handler

            def _make_caller(
                current_interceptor: ToolInterceptor,
                next_h: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
            ) -> Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]]:
                return lambda c: current_interceptor.intercept(c, next_h)

            handler = _make_caller(interceptor, prev_handler)

        return await handler(ctx)
