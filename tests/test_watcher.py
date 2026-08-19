"""Tests for filesystem plugin watcher."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.plugins.loader import PluginLoader
from harness.plugins.watcher import PluginFileEventHandler, PluginWatcher


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginWatcher:
    async def test_watcher_event_handler(self, tmp_path: Path) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        loader = PluginLoader([tmp_path])
        loop = asyncio.get_running_loop()

        handler = PluginFileEventHandler(loader, lifecycle, loop)

        # Mock directory creation event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(tmp_path / "new_plugin")

        (tmp_path / "new_plugin").mkdir()
        (tmp_path / "new_plugin" / "plugin.json").write_text('{"name": "watcher-test", "version": "1.0.0"}')

        handler.on_created(mock_event)
        await asyncio.sleep(0.1)

        assert "watcher-test" in lifecycle.plugins

        # Test modify event
        mod_event = MagicMock()
        mod_event.is_directory = False
        mod_event.src_path = str(tmp_path / "new_plugin" / "plugin.json")
        handler.on_modified(mod_event)
        await asyncio.sleep(0.1)

        # Test delete event
        del_event = MagicMock()
        del_event.is_directory = True
        del_event.src_path = str(tmp_path / "new_plugin")
        handler.on_deleted(del_event)
        await asyncio.sleep(0.1)

    async def test_watcher_start_stop(self, tmp_path: Path) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        loader = PluginLoader([tmp_path])

        watcher = PluginWatcher([tmp_path], loader, lifecycle)
        watcher.start()
        assert watcher._observer is not None
        watcher.stop()
        assert watcher._observer is None
