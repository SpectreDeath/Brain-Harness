"""Tests for RepoConverter and ConvertedPlugin."""

from pathlib import Path

import pytest

from harness.ingestion.converter import ConvertedPlugin, RepoConverter
from harness.kernel.context import ServiceContext
from harness.plugins.manifest import IsolationMode, PluginManifest


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepoConverter:
    async def test_convert_and_run_subprocess_plugin(self, tmp_path: Path) -> None:
        # Create a mock repo
        main_py = tmp_path / "main.py"
        main_py.write_text(
            """
def ping(message: str) -> str:
    return f"pong: {message}"
"""
        )

        manifest = PluginManifest(
            name="converted-ping-plugin",
            version="1.0.0",
            entrypoint="main.py",
            provides=["tool.ping"],
            isolation=IsolationMode.SUBPROCESS,
        )

        converter = RepoConverter()
        plugin = converter.convert(tmp_path, manifest)

        assert isinstance(plugin, ConvertedPlugin)
        assert plugin.name == "converted-ping-plugin"
        assert len(plugin.provides) == 1
        assert (tmp_path / "plugin.json").exists()

        # Test plugin lifecycle
        ctx = ServiceContext()
        await plugin.on_load(ctx)
        assert ctx.has(plugin.provides[0])

        await plugin.on_enable()
        assert plugin.executor is not None
        assert plugin.executor.is_running

        # Test invocation via sandbox
        call_res = await plugin.call("ping", {"message": "test"})
        assert call_res == {"status": "ok", "result": "pong: test"}

        await plugin.on_disable()
        assert not plugin.executor.is_running

        await plugin.on_unload()
