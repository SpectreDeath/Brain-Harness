"""Tests for EcosystemBridgePlugin base class."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.bridges.base import EcosystemBridgePlugin
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolRegistryPlugin

DUMMY_BRIDGE_KEY: ServiceKey[DummyBridge] = ServiceKey("bridge.dummy")


class DummyBridge(EcosystemBridgePlugin[str]):
    project_name = "dummy-repo"
    env_var = "DUMMY_PATH"
    service_key = DUMMY_BRIDGE_KEY

    @property
    def name(self) -> str:
        return "bridge.dummy"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def init_substrate(self, root_path: Path) -> str:
        return f"substrate_at_{root_path.name}"

    async def mount_tools(self) -> None:
        if self._ctx and self._ctx.has(TOOL_REGISTRY_KEY):
            registry: ToolRegistry = self._ctx.require(TOOL_REGISTRY_KEY)
            registry.register(
                name="dummy.ping",
                description="Dummy tool",
                executor=lambda: "pong",
                provider=self.name,
            )


@pytest.mark.unit
@pytest.mark.asyncio
class TestEcosystemBridgeBase:
    async def test_bridge_lifecycle_and_tool_mounting(self, tmp_path: Path) -> None:
        ctx = ServiceContext()
        tool_plugin = ToolRegistryPlugin()
        await tool_plugin.on_load(ctx)

        bridge_root = tmp_path / "dummy-repo"
        bridge_root.mkdir()

        bridge = DummyBridge(override_path=bridge_root)
        assert bridge.name == "bridge.dummy"
        assert bridge.provides == [DUMMY_BRIDGE_KEY]
        assert bridge.requires == [TOOL_REGISTRY_KEY]
        assert bridge.trusted is True

        # Load
        await bridge.on_load(ctx)
        assert ctx.has(DUMMY_BRIDGE_KEY)

        # Enable
        await bridge.on_enable()
        assert bridge.substrate == "substrate_at_dummy-repo"

        tools: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)
        assert "dummy.ping" in tools
        res = await tools.invoke("dummy.ping", {})
        assert res == {"status": "ok", "result": "pong"}

        # Disable
        await bridge.on_disable()
        assert "dummy.ping" not in tools

        # Unload
        await bridge.on_unload()
        assert bridge.substrate is None

    async def test_declarative_tool_specs_bridge(self, tmp_path: Path) -> None:
        from harness.services.tools import ToolSpec

        decl_key = ServiceKey[str]("bridge.declarative")

        class DeclarativeBridge(EcosystemBridgePlugin[str]):
            project_name = "decl-repo"
            env_var = "DECL_PATH"
            service_key = decl_key

            @property
            def name(self) -> str:
                return "bridge.decl"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def init_fallback_substrate(self) -> str:
                return "fallback_substrate"

            async def get_tool_specs(self) -> list[ToolSpec]:
                async def _echo(text: str) -> str:
                    return f"echo: {text}"

                return [
                    ToolSpec(
                        name="decl.echo",
                        description="Declarative echo tool",
                        executor=_echo,
                        provider=self.name,
                    )
                ]

        ctx = ServiceContext()
        tool_plugin = ToolRegistryPlugin()
        await tool_plugin.on_load(ctx)

        bridge = DeclarativeBridge()
        await bridge.on_load(ctx)
        assert bridge.substrate == "fallback_substrate"

        await bridge.on_enable()
        tools: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)
        assert "decl.echo" in tools

        res = await tools.invoke("decl.echo", {"text": "hello"})
        assert res == {"status": "ok", "result": "echo: hello"}

        await bridge.on_disable()
        assert "decl.echo" not in tools

        await bridge.on_unload()
        assert bridge.substrate is None
