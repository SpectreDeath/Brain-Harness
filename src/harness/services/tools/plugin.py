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

    async def on_load(self, ctx: ServiceContext) -> None:
        bus = ctx.optional(EVENT_BUS_KEY)
        self._registry = ToolRegistry(event_bus=bus)
        ctx.provide(TOOL_REGISTRY_KEY, self._registry, provider=self.name)
        logger.info("Tool registry service registered", telemetry=bus is not None)

    async def on_unload(self) -> None:
        self._registry = None


# Module singleton export (Rule 45)
plugin = ToolRegistryPlugin()
