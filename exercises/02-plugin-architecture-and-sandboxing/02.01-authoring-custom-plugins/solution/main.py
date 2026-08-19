"""Exercise 02.01: Authoring Custom Plugins (Solution)."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry


class TextTransformPlugin(HarnessPlugin):
    def __init__(self) -> None:
        self._ctx: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "tools.text_transform"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    async def on_enable(self) -> None:
        ctx = self._ctx or (self.context if hasattr(self, "context") else None)
        if ctx:
            registry: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)
            registry.register(
                name="text.reverse",
                description="Reverse input text string",
                executor=lambda text="": str(text)[::-1],
                provider=self.name,
            )
