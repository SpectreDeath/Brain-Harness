"""Exercise 01.02: Topological Plugin Lifecycle (Solution)."""

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
        return [SERVICE_A_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SERVICE_A_KEY, "Service A Value", provider=self.name)


class PluginB(HarnessPlugin):
    @property
    def name(self) -> str:
        return "plugin.b"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [SERVICE_A_KEY]


async def run_lifecycle() -> PluginLifecycle:
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    p_a = PluginA()
    p_b = PluginB()

    lifecycle.discover(p_b)
    lifecycle.discover(p_a)

    await lifecycle.load(p_b.name)
    await lifecycle.load(p_a.name)

    await lifecycle.validate(p_b.name)
    await lifecycle.validate(p_a.name)

    await lifecycle.enable_all()

    return lifecycle
