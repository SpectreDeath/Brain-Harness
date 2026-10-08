"""Central tool registry managing tool schemas, enablement, and execution dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.events.types import EventType, tool_event
from harness.kernel.context import ServiceKey
from harness.services.tools.models import ToolExecutionContext, ToolExecutor, ToolSpec
from harness.services.tools.pipeline import ToolExecutionPipeline

if TYPE_CHECKING:
    from harness.events.bus import EventBus
    from harness.services.tools.interceptors import ToolInterceptor

logger = structlog.get_logger()

TOOL_REGISTRY_KEY: ServiceKey[ToolRegistry] = ServiceKey("tools.registry")


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
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            logger.info("Tool unregistered", tool=name)
            return True
        return False

    def unregister_all_from(self, provider: str) -> list[str]:
        """Remove all tools registered by a given plugin."""
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
        """Invoke a tool by name through the interceptor pipeline with telemetry and error isolation."""
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
        """Get tool schemas in OpenAI function-calling format."""
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
