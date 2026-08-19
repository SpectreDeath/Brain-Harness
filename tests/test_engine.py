"""Tests for PluginIngestionEngine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.ingestion.pipeline import PluginIngestionEngine
from harness.plugins.manifest import IsolationMode
from harness.plugins.sandboxed import SandboxedPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginIngestionEngine:
    async def test_ingest_local_directory(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "mock_plugin"
        source_dir.mkdir()
        (source_dir / "plugin.json").write_text(
            json.dumps({
                "name": "engine_test_plugin",
                "version": "1.2.3",
                "description": "Created by engine test",
                "entrypoint": "main.py",
            })
        )
        (source_dir / "main.py").write_text("def test(): return 'ok'\n")

        engine = PluginIngestionEngine(plugin_dir=tmp_path / "plugins")
        plugin = await engine.ingest(source_dir, isolation=IsolationMode.IN_PROCESS)

        assert isinstance(plugin, SandboxedPlugin)
        assert plugin.name == "engine_test_plugin"
        assert plugin.version == "1.2.3"
        assert plugin.manifest.isolation == IsolationMode.IN_PROCESS

    async def test_engine_cached_management(self, tmp_path: Path) -> None:
        plugin_cache = tmp_path / "cached_plugins"
        plugin_cache.mkdir()

        cached_item = plugin_cache / "cached_one"
        cached_item.mkdir()
        (cached_item / "plugin.json").write_text('{"name": "cached_one", "version": "1.0.0"}')

        engine = PluginIngestionEngine(plugin_dir=plugin_cache)
        cached_list = engine.list_cached()
        assert len(cached_list) == 1
        assert cached_list[0]["name"] == "cached_one"

        assert engine.remove_cached("cached_one") is True
        assert not cached_item.exists()
