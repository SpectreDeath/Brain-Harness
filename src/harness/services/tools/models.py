"""Tool data models, execution context, and schema reflection representations."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
import inspect
import types
from typing import TYPE_CHECKING, Any, Union, get_type_hints

import structlog

if TYPE_CHECKING:
    from harness.events.bus import EventBus

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
        """Construct a ToolSpec by introspecting a Python callable."""
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
