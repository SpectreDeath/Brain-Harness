"""Tool registry service — central registry of callable tools.

Tools are the primary interface between the agent loop and plugins.
Each tool has a name, description, JSON Schema for parameters, and
an async execute method. Plugins register tools when they're enabled
and tools are automatically removed when plugins are disabled.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, tool_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

# Canonical service key defined before downstream plugin imports to break circular dependencies
TOOL_REGISTRY_KEY: ServiceKey[ToolRegistry] = ServiceKey("tools.registry")

logger = structlog.get_logger()

# Type for tool execution functions
ToolExecutor = Callable[..., Awaitable[Any]]


@dataclass
class ToolExecutionContext:
    """Execution context passed through the tool interceptor pipeline."""

    name: str
    """Name of the tool being executed."""

    spec: ToolSpec
    """The registered ToolSpec."""

    params: dict[str, Any] = field(default_factory=dict)
    """Parameters passed to the executor."""

    timeout: float = 30.0
    """Maximum execution duration in seconds."""

    event_bus: EventBus | None = None
    """Optional event bus for telemetry emission."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible context dictionary for custom middleware."""


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
                logger.warning("Tool access denied by policy", tool=ctx.name, realm=caller_realm, allowed=ctx.spec.allowed_realms)
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
            # Fallback executor guard
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


@dataclass
class ToolSpec:
    """Describes a registered tool."""

    name: str
    """Unique tool name (e.g., 'git.clone', 'web.search')."""

    description: str
    """Human-readable description of what the tool does."""

    parameters_schema: dict[str, Any] = field(default_factory=dict)
    """JSON Schema describing the tool's input parameters."""

    provider: str = ""
    """Name of the plugin that registered this tool."""

    executor: ToolExecutor | None = None
    """The async callable that executes the tool."""

    returns_schema: dict[str, Any] = field(default_factory=dict)
    """JSON Schema describing the tool's output."""

    enabled: bool = True
    """Whether this tool is active and exposed to the LLM agent."""

    allowed_realms: list[str] | None = None
    """List of isolation realms permitted to invoke this tool (None = unrestricted)."""

    rate_limit_per_minute: float | None = None
    """Maximum allowable invocations per minute (None = unrestricted)."""

    cache_ttl: float | None = None
    """Cache duration in seconds for idempotent executions (None = no caching)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert ToolSpec to standard dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "provider": self.provider,
            "enabled": self.enabled,
            "parameters": list(self.parameters_schema.get("properties", {}).keys())
            if self.parameters_schema
            else [],
            "parameters_schema": self.parameters_schema,
            "returns_schema": self.returns_schema,
            "allowed_realms": self.allowed_realms,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "cache_ttl": self.cache_ttl,
        }

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert ToolSpec to OpenAI/OpenAPI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
                or {"type": "object", "properties": {}},
            },
        }

    def to_mcp_tool(self) -> dict[str, Any]:
        """Convert ToolSpec to Model Context Protocol (MCP) tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters_schema or {"type": "object", "properties": {}},
        }


    @classmethod
    def from_callable(
        cls,
        func: Callable[..., Any],
        *,
        name: str | None = None,
        provider: str = "",
        description: str | None = None,
        enabled: bool = True,
        allowed_realms: list[str] | None = None,
        rate_limit_per_minute: float | None = None,
        cache_ttl: float | None = None,
    ) -> ToolSpec:
        """Construct a ToolSpec by introspecting a Python callable.

        Extracts docstrings, function signatures, and type annotations into
        a standard JSON Schema parameters object.

        Args:
            func: Python function or callable.
            name: Optional tool name (defaults to func.__name__).
            provider: Owning plugin or provider name.
            description: Optional tool description (defaults to func docstring).
            enabled: Initial enabled state.
            allowed_realms: Optional list of isolation realms authorized to call this tool.
            rate_limit_per_minute: Optional maximum calls per minute limit.
            cache_ttl: Optional caching duration in seconds for idempotent results.

        Returns:
            Configured ToolSpec with JSON Schema properties.
        """
        import inspect
        import types
        from typing import Union, get_type_hints

        tool_name = str(name or getattr(func, "__name__", "custom_tool"))
        doc = description or inspect.getdoc(func) or f"Execute {tool_name}"

        properties: dict[str, Any] = {}
        required: list[str] = []

        try:
            sig = inspect.signature(func)
            try:
                hints = get_type_hints(func)
            except Exception:
                hints = {}

            type_map: dict[type, str] = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                dict: "object",
                list: "array",
            }

            def _resolve_type(h: Any) -> str:
                if h is inspect.Parameter.empty or h is None:
                    return "string"
                if h in type_map:
                    return type_map[h]
                if hasattr(types, "UnionType") and isinstance(h, types.UnionType):
                    args = [a for a in getattr(h, "__args__", ()) if a is not type(None)]
                    if args:
                        return _resolve_type(args[0])
                    return "string"
                origin = getattr(h, "__origin__", None)
                if origin is not None:
                    if origin in (list, set, tuple):
                        return "array"
                    if origin is dict:
                        return "object"
                    if origin is Union or (hasattr(types, "UnionType") and origin is types.UnionType):
                        args = [a for a in getattr(h, "__args__", ()) if a is not type(None)]
                        if args:
                            return _resolve_type(args[0])
                if isinstance(h, type):
                    if issubclass(h, (list, set, tuple)):
                        return "array"
                    if issubclass(h, dict):
                        return "object"
                    if issubclass(h, bool):
                        return "boolean"
                    if issubclass(h, int):
                        return "integer"
                    if issubclass(h, float):
                        return "number"
                    if issubclass(h, str):
                        return "string"
                return "string"

            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue
                if param.kind in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    continue

                hint = hints.get(param_name, param.annotation)
                param_type = _resolve_type(hint)

                prop_def: dict[str, Any] = {"type": param_type}
                if param.default is not inspect.Parameter.empty:
                    prop_def["default"] = param.default
                else:
                    required.append(param_name)

                properties[param_name] = prop_def

        except Exception as e:
            logger.debug(
                "Failed introspecting function signature for tool schema",
                tool=tool_name,
                error=str(e),
            )

        parameters_schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters_schema["required"] = required

        return cls(
            name=tool_name,
            description=doc,
            parameters_schema=parameters_schema,
            provider=provider,
            executor=func,
            enabled=enabled,
            allowed_realms=allowed_realms,
            rate_limit_per_minute=rate_limit_per_minute,
            cache_ttl=cache_ttl,
        )



class ToolRegistry:
    """Central registry of tools available to the agent loop.

    Plugins register tools here during ``on_enable()``. The registry
    provides the tool schemas to the LLM (for function calling), manages
    execution interceptors/telemetry, and dispatches invocations to executors.
    """

    def __init__(
        self,
        event_bus: EventBus | None = None,
        pipeline: ToolExecutionPipeline | None = None,
    ) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._event_bus = event_bus
        self._pipeline: ToolExecutionPipeline = (
            pipeline if pipeline is not None else ToolExecutionPipeline()
        )

    @property
    def event_bus(self) -> EventBus | None:
        """Attached event bus for telemetry."""
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus: EventBus | None) -> None:
        self._event_bus = bus

    @property
    def pipeline(self) -> ToolExecutionPipeline:
        """The active tool execution interceptor pipeline."""
        return self._pipeline

    def add_interceptor(
        self, interceptor: ToolInterceptor, position: int | None = None
    ) -> None:
        """Add a middleware interceptor to the execution pipeline."""
        self._pipeline.add_interceptor(interceptor, position=position)

    def enable_tool(self, name: str) -> bool:
        """Enable a specific tool by name."""
        if name in self._tools:
            self._tools[name].enabled = True
            logger.info("Tool enabled", tool=name)
            return True
        return False

    def disable_tool(self, name: str) -> bool:
        """Disable a specific tool by name without unregistering it."""
        if name in self._tools:
            self._tools[name].enabled = False
            logger.info("Tool disabled", tool=name)
            return True
        return False

    def toggle_tool(self, name: str, enabled: bool | None = None) -> bool:
        """Toggle a tool's enablement state."""
        if name in self._tools:
            if enabled is None:
                self._tools[name].enabled = not self._tools[name].enabled
            else:
                self._tools[name].enabled = enabled
            logger.info("Tool toggled", tool=name, enabled=self._tools[name].enabled)
            return True
        return False

    def is_tool_enabled(self, name: str) -> bool:
        """Check if a tool is registered and enabled."""
        spec = self._tools.get(name)
        return spec is not None and spec.enabled

    def register_tool(self, spec: ToolSpec) -> None:
        """Register a pre-constructed ToolSpec."""
        if spec.name in self._tools:
            logger.warning(
                "Tool already registered, overwriting",
                tool=spec.name,
                old_provider=self._tools[spec.name].provider,
                new_provider=spec.provider,
            )
        self._tools[spec.name] = spec
        logger.info("Tool registered", tool=spec.name, provider=spec.provider, enabled=spec.enabled)

    def register(
        self,
        name: str | ToolSpec,
        description: str = "",
        executor: ToolExecutor | None = None,
        *,
        parameters_schema: dict[str, Any] | None = None,
        provider: str = "",
        returns_schema: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> None:
        """Register a tool.

        Accepts either individual parameters or a pre-configured ToolSpec.
        """
        if isinstance(name, ToolSpec):
            self.register_tool(name)
            return

        if executor is None:
            raise ValueError("executor must be provided when registering by name")

        if name in self._tools:
            logger.warning(
                "Tool already registered, overwriting",
                tool=name,
                old_provider=self._tools[name].provider,
                new_provider=provider,
            )

        self._tools[name] = ToolSpec(
            name=name,
            description=description,
            parameters_schema=parameters_schema or {},
            provider=provider,
            executor=executor,
            returns_schema=returns_schema or {},
            enabled=enabled,
        )
        logger.info("Tool registered", tool=name, provider=provider, enabled=enabled)

    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.

        Returns:
            True if the tool was found and removed.
        """
        if name in self._tools:
            del self._tools[name]
            logger.info("Tool unregistered", tool=name)
            return True
        return False

    def unregister_all_from(self, provider: str) -> list[str]:
        """Remove all tools registered by a given plugin.

        Args:
            provider: Plugin name whose tools to remove.

        Returns:
            List of removed tool names.
        """
        to_remove = [
            name for name, spec in self._tools.items() if spec.provider == provider
        ]
        for name in to_remove:
            del self._tools[name]

        if to_remove:
            logger.info(
                "Tools unregistered for plugin",
                provider=provider,
                tools=to_remove,
            )
        return to_remove

    async def invoke(
        self,
        name: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool by name through the interceptor pipeline with telemetry and error isolation.

        Args:
            name: Tool name.
            params: Parameters to pass to the executor.
            timeout: Maximum execution duration in seconds.
            metadata: Optional execution metadata (e.g. caller realm, tracing info).

        Returns:
            Dict with ``status`` ("ok" or "error") and ``result`` or ``error``.
        """
        spec = self._tools.get(name)
        if spec is None:
            err = f"Tool not found: {name}"
            logger.warning("Tool invocation failed", tool=name, error=err)
            if self._event_bus:
                await self._event_bus.emit(
                    tool_event(EventType.TOOL_ERROR, name, source="tool.registry", error=err)
                )
            return {"status": "error", "error": err}

        if not spec.enabled:
            err = f"Tool '{name}' is currently disabled"
            logger.warning("Tool invocation rejected (disabled)", tool=name)
            if self._event_bus:
                await self._event_bus.emit(
                    tool_event(
                        EventType.TOOL_ERROR,
                        name,
                        source=spec.provider or "tool.registry",
                        error=err,
                    )
                )
            return {"status": "error", "error": err}

        ctx = ToolExecutionContext(
            name=name,
            spec=spec,
            params=params or {},
            timeout=timeout,
            event_bus=self._event_bus,
            metadata=metadata or {},
        )

        return await self._pipeline.execute(ctx)

    def get(self, name: str) -> ToolSpec | None:
        """Get a tool spec by name."""
        return self._tools.get(name)

    def list_tools(
        self,
        *,
        enabled_only: bool = False,
        provider: str | None = None,
    ) -> list[ToolSpec]:
        """List registered tools, optionally filtered by enablement or provider."""
        tools = list(self._tools.values())
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        if provider:
            tools = [t for t in tools if t.provider == provider]
        return tools

    def get_schemas(self, *, enabled_only: bool = True) -> list[dict[str, Any]]:
        """Get tool schemas in OpenAI function-calling format.

        By default, filters to only enabled tools so LLM prompts remain lean.
        """
        tools = self.list_tools(enabled_only=enabled_only)
        return [spec.to_openai_tool() for spec in tools]

    to_openai_tools = get_schemas
    to_definitions = get_schemas

    def to_catalog(
        self,
        *,
        enabled_only: bool = False,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """Export registered tools in standard dictionary catalog format."""
        tools = self.list_tools(enabled_only=enabled_only, provider=provider)
        return [spec.to_dict() for spec in tools]

    def to_mcp_tools(
        self,
        *,
        enabled_only: bool = False,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """Export registered tools in Model Context Protocol (MCP) format."""
        tools = self.list_tools(enabled_only=enabled_only, provider=provider)
        return [spec.to_mcp_tool() for spec in tools]


    @property
    def count(self) -> int:
        """Number of registered tools."""
        return len(self._tools)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_tool(self, name: str) -> ToolSpec | None:
        """Get a registered ToolSpec by name."""
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={self.count})"


class ToolRegistryPlugin(HarnessPlugin):
    """Built-in plugin that provides the tool registry service."""

    def __init__(self) -> None:
        self._registry: ToolRegistry | None = None

    @property
    def name(self) -> str:
        return "tools.registry"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Central tool registry for agent tool dispatch"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        bus = ctx.optional(EVENT_BUS_KEY)
        self._registry = ToolRegistry(event_bus=bus)
        ctx.provide(TOOL_REGISTRY_KEY, self._registry, provider=self.name)
        logger.info("Tool registry service registered", telemetry=bus is not None)

    async def on_unload(self) -> None:
        self._registry = None
