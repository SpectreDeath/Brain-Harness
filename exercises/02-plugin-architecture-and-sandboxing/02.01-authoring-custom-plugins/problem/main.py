"""Exercise 02.01: Authoring Custom Plugins (Problem)."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceKey
from harness.plugins.base import HarnessPlugin


class TextTransformPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "tools.text_transform"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        # TODO: Require TOOL_REGISTRY_KEY
        return []

    async def on_enable(self) -> None:
        # TODO: Get tool registry from self.context and register tool "text.reverse"
        # Executor should reverse the string argument: text[::-1]
        pass
