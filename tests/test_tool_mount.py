"""Unit tests for ToolMountMixin."""

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolSpec


class SampleMountPlugin(ToolMountMixin, HarnessPlugin):
    @property
    def name(self) -> str:
        return "sample_mount"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey]:
        return []

    @property
    def requires(self) -> list[ServiceKey]:
        return self.tool_mount_requires()

    async def on_load(self, ctx: ServiceContext) -> None:
        self._mount_ctx = ctx
        self._mount_name = self.name

    async def on_enable(self) -> None:
        async def dummy_tool(x: int) -> int:
            return x * 2

        spec = ToolSpec(
            name="sample_mount.double",
            description="Double a number",
            executor=dummy_tool,
        )
        await self.mount_tools([spec])

    async def on_disable(self) -> None:
        await self.unmount_tools()


@pytest.mark.unit
@pytest.mark.asyncio
class TestToolMountMixin:
    async def test_tool_mount_and_unmount(self) -> None:
        ctx = ServiceContext()
        reg = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, reg)

        plugin = SampleMountPlugin()
        assert TOOL_REGISTRY_KEY in plugin.requires

        await plugin.on_load(ctx)
        await plugin.on_enable()

        assert "sample_mount.double" in reg
        res = await reg.invoke("sample_mount.double", {"x": 5})
        assert res == {"status": "ok", "result": 10}

        await plugin.on_disable()
        assert "sample_mount.double" not in reg

    async def test_tool_mount_without_registry(self) -> None:
        ctx = ServiceContext()
        plugin = SampleMountPlugin()
        await plugin.on_load(ctx)
        # Should no-op cleanly without throwing
        await plugin.on_enable()
        await plugin.on_disable()
