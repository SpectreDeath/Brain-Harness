"""Tool execution interceptors providing telemetry, access control, rate limiting, and timeout guards."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import inspect
import json
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog

from harness.events.types import EventType, tool_event
from harness.services.tools.models import ToolExecutionContext

logger = structlog.get_logger()


class ToolInterceptor(ABC):
    """Abstract middleware interceptor for the tool execution pipeline."""

    @abstractmethod
    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Wrap, inspect, or modify tool execution."""


class TelemetryInterceptor(ToolInterceptor):
    """Emits TOOL_INVOKED, TOOL_RESULT, and TOOL_ERROR events on the event bus."""

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        provider = ctx.spec.provider or "tool.registry"
        if ctx.event_bus:
            await ctx.event_bus.emit(
                tool_event(
                    EventType.TOOL_INVOKED,
                    ctx.name,
                    source=provider,
                    params=ctx.params,
                )
            )

        result = await next_handler(ctx)

        if ctx.event_bus:
            if result.get("status") == "ok":
                await ctx.event_bus.emit(
                    tool_event(
                        EventType.TOOL_RESULT,
                        ctx.name,
                        source=provider,
                        result=result.get("result"),
                    )
                )
            else:
                await ctx.event_bus.emit(
                    tool_event(
                        EventType.TOOL_ERROR,
                        ctx.name,
                        source=provider,
                        error=str(result.get("error", "Unknown error")),
                    )
                )

        return result


class AccessControlInterceptor(ToolInterceptor):
    """Enforces realm-based or caller-based access control policies on tool invocations."""

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if ctx.spec.allowed_realms is not None and len(ctx.spec.allowed_realms) > 0:
            caller_realm = ctx.metadata.get("realm") or ctx.metadata.get("caller_realm")
            if caller_realm not in ctx.spec.allowed_realms:
                err = f"Access denied: realm '{caller_realm}' is not authorized to execute tool '{ctx.name}'"
                logger.warning(
                    "Tool access denied by policy",
                    tool=ctx.name,
                    realm=caller_realm,
                    allowed=ctx.spec.allowed_realms,
                )
                if ctx.event_bus:
                    await ctx.event_bus.emit(
                        tool_event(
                            EventType.TOOL_ERROR,
                            ctx.name,
                            source=ctx.spec.provider or "access_control",
                            error=err,
                        )
                    )
                return {"status": "error", "error": err}

        return await next_handler(ctx)


class RateLimitInterceptor(ToolInterceptor):
    """Token-bucket rate limiter guarding tool execution frequency."""

    def __init__(self, default_rate_per_minute: float | None = None) -> None:
        self.default_rate = default_rate_per_minute
        self._tokens: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}

    def reset(self) -> None:
        """Reset rate limiter token buckets."""
        self._tokens.clear()
        self._last_refill.clear()

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        rate_limit = ctx.spec.rate_limit_per_minute or self.default_rate
        if rate_limit is not None and rate_limit > 0:
            now = time.time()
            key = ctx.name
            capacity = float(rate_limit)
            refill_rate = capacity / 60.0

            last = self._last_refill.get(key, now)
            current_tokens = self._tokens.get(key, capacity)
            elapsed = max(0.0, now - last)

            current_tokens = min(capacity, current_tokens + elapsed * refill_rate)
            self._last_refill[key] = now

            if current_tokens < 1.0:
                self._tokens[key] = current_tokens
                err = f"Rate limit exceeded for tool '{ctx.name}' ({rate_limit}/min)"
                logger.warning("Tool rate limit exceeded", tool=ctx.name, rate_limit=rate_limit)
                if ctx.event_bus:
                    await ctx.event_bus.emit(
                        tool_event(
                            EventType.TOOL_ERROR,
                            ctx.name,
                            source=ctx.spec.provider or "rate_limiter",
                            error=err,
                        )
                    )
                return {"status": "error", "error": err}

            self._tokens[key] = current_tokens - 1.0

        return await next_handler(ctx)


class MemoizationInterceptor(ToolInterceptor):
    """Caches idempotent tool execution results based on parameter signatures."""

    def __init__(self, default_ttl: float | None = None) -> None:
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

    def _make_key(self, tool_name: str, params: dict[str, Any]) -> str:
        try:
            serialized = json.dumps(params, sort_keys=True, default=str)
        except Exception:
            serialized = str(params)
        return f"{tool_name}:{serialized}"

    def clear(self) -> None:
        """Clear cached results."""
        self._cache.clear()

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        ttl = ctx.spec.cache_ttl or ctx.metadata.get("cache_ttl") or self.default_ttl
        if ttl is not None and ttl > 0:
            cache_key = self._make_key(ctx.name, ctx.params)
            now = time.time()
            if cache_key in self._cache:
                entry, cached_at = self._cache[cache_key]
                if now - cached_at < ttl:
                    logger.debug("Tool execution memoization cache hit", tool=ctx.name)
                    hit_res = dict(entry)
                    hit_res["cached"] = True
                    return hit_res

            res = await next_handler(ctx)
            if res.get("status") == "ok":
                self._cache[cache_key] = (res, now)
            return res

        return await next_handler(ctx)


class SchemaValidationInterceptor(ToolInterceptor):
    """Validates required input parameters against the tool schema."""

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if ctx.spec.parameters_schema and "required" in ctx.spec.parameters_schema:
            missing = [
                r for r in ctx.spec.parameters_schema["required"] if r not in ctx.params
            ]
            if missing:
                err = f"Missing required parameter(s): {missing}"
                logger.warning("Tool schema validation failed", tool=ctx.name, missing=missing)
                return {"status": "error", "error": err}

        return await next_handler(ctx)


class TimeoutGuardInterceptor(ToolInterceptor):
    """Executes the tool with timeout protection, sync/async normalization, and error isolation."""

    async def intercept(
        self,
        ctx: ToolExecutionContext,
        next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if ctx.spec.executor is None:
            err = f"Tool has no executor: {ctx.name}"
            logger.error("Tool invocation failed", tool=ctx.name, error=err)
            return {"status": "error", "error": err}

        try:
            if inspect.iscoroutinefunction(ctx.spec.executor):
                res = await asyncio.wait_for(
                    ctx.spec.executor(**ctx.params), timeout=ctx.timeout
                )
            else:
                raw_res = ctx.spec.executor(**ctx.params)
                if asyncio.iscoroutine(raw_res):
                    res = await asyncio.wait_for(raw_res, timeout=ctx.timeout)
                else:
                    res = raw_res
            return {"status": "ok", "result": res}

        except asyncio.TimeoutError:
            err = f"Tool '{ctx.name}' timed out after {ctx.timeout}s"
            logger.error("Tool invocation timeout", tool=ctx.name, timeout=ctx.timeout)
            return {"status": "error", "error": err}

        except Exception as e:
            err = str(e)
            logger.error("Tool invocation failed", tool=ctx.name, error=err)
            return {"status": "error", "error": err}
