"""IoC plugin registering the central ToolRegistry into the micro-kernel container.

Adheres to:
- Rule 1: Everything is a plugin.
- Rule 2: Typed service keys.
- Rule 45: Plugin module singleton export (plugin = ToolRegistryPlugin()).
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.events.bus import EVENT_BUS_KEY
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.tools.registry import TOOL_REGISTRY_KEY, ToolRegistry

logger = structlog.get_logger()


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

    @property
    def trust_justification(self) -> str:
        return "Core kernel tool registry managing tool reflection, alias resolution, and dispatch"

    async def on_load(self, ctx: ServiceContext) -> None:
        bus = ctx.optional(EVENT_BUS_KEY)
        self._registry = ToolRegistry(event_bus=bus)
        from harness.services.rea_toolkit import REA_TOOL_ALIASES
        for alias, target in REA_TOOL_ALIASES.items():
            self._registry.register_alias(alias, target)

        # Apply persisted tool enablement state from .harness/tool_state.json if present
        from pathlib import Path
        import json
        tool_state_file = Path(".harness/tool_state.json")
        if tool_state_file.exists():
            try:
                state = json.loads(tool_state_file.read_text(encoding="utf-8"))
                for t in state.get("disabled_tools", []):
                    self._registry.disable_tool(t)
                for t in state.get("enabled_tools", []):
                    self._registry.enable_tool(t)
            except Exception as e:
                logger.debug("Failed to apply persisted tool state", error=str(e))

        ctx.provide(TOOL_REGISTRY_KEY, self._registry, provider=self.name)
        logger.info("Tool registry service registered", telemetry=bus is not None)

    async def on_unload(self) -> None:
        self._registry = None


# Module singleton export (Rule 45)
plugin = ToolRegistryPlugin()
