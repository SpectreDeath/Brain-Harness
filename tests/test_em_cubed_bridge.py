"""Tests for Em-Cubed ecosystem bridge."""

from pathlib import Path

import pytest

from harness.bridges.em_cubed import EM_CUBED_BRIDGE_KEY, EmCubedPlugin
from harness.kernel.context import ServiceContext
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmCubedBridge:
    async def test_em_cubed_plugin_lifecycle(self) -> None:
        ctx = ServiceContext()
        tool_plugin = ToolRegistryPlugin()
        await tool_plugin.on_load(ctx)

        bridge = EmCubedPlugin()
        assert bridge.name == "bridge.em_cubed"
        assert bridge.provides == [EM_CUBED_BRIDGE_KEY]

        await bridge.on_load(ctx)
        assert ctx.has(EM_CUBED_BRIDGE_KEY)

        await bridge.on_enable()
        _ = ctx.require(TOOL_REGISTRY_KEY)

        # Check direct execution wrapper fallback
        res = await bridge.execute_surface("python", "x = 1 + 1")
        assert "status" in res

        await bridge.on_disable()
        await bridge.on_unload()


class TestEcosystemLocator:
    def test_locator_explicit_path(self, tmp_path: Path) -> None:
        from harness.bridges.locator import EcosystemLocator

        mock_em = tmp_path / "em-cubed"
        mock_em.mkdir()

        resolved = EcosystemLocator.locate("em-cubed", explicit_path=mock_em)
        assert resolved == mock_em.resolve()

    def test_locator_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from harness.bridges.locator import EcosystemLocator

        mock_mem = tmp_path / "CustomMemtext"
        mock_mem.mkdir()
        monkeypatch.setenv("MEMTEXT_PATH", str(mock_mem))

        resolved = EcosystemLocator.locate_memtext()
        assert resolved == mock_mem.resolve()

    def test_locator_status(self) -> None:
        from harness.bridges.locator import EcosystemLocator

        status = EcosystemLocator.status()
        assert "em-cubed" in status
        assert "Memtext" in status
        assert "Skill Flywheel" in status
        assert "env_var" in status["em-cubed"]
