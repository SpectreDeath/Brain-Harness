"""Exercise 01.02: Topological Plugin Lifecycle (Problem)."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle
from harness.plugins.base import HarnessPlugin

SERVICE_A_KEY: ServiceKey[str] = ServiceKey("service.a")


class PluginA(HarnessPlugin):
    @property
    def name(self) -> str:
        return "plugin.a"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        # TODO: Return SERVICE_A_KEY
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        # TODO: Provide "Service A Value" under SERVICE_A_KEY
        pass


class PluginB(HarnessPlugin):
    @property
    def name(self) -> str:
        return "plugin.b"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        # TODO: Declare requirement on SERVICE_A_KEY
        return []


async def run_lifecycle() -> PluginLifecycle:
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    # TODO: Discover both plugins
    # TODO: Load both plugins
    # TODO: Enable all plugins and return lifecycle
    return lifecycle
