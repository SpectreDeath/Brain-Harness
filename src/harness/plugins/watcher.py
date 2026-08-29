"""Plugin watcher — monitors plugin directories for live hot-reloading and comment triggers.

Uses watchdog to observe file changes in configured plugin directories.
Automatically loads newly added plugins, hot-reloads modified plugins,
unloads deleted plugins, and scans for autonomous comment markers (# HARNESS: ...).
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from harness.kernel.lifecycle import PluginLifecycle
from harness.plugins.loader import PluginLoader

logger = structlog.get_logger()


class PluginFileEventHandler(FileSystemEventHandler):
    """Handles watchdog filesystem events and triggers lifecycle updates."""

    def __init__(
        self,
        loader: PluginLoader,
        lifecycle: PluginLifecycle,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.loader = loader
        self.lifecycle = lifecycle
        self.loop = loop
        self._dir_to_plugins: dict[str, set[str]] = {}

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            src_str = os.fsdecode(event.src_path)
            logger.info("New plugin directory detected", path=src_str)
            self._trigger_reload(Path(src_str))

    def on_modified(self, event: FileSystemEvent) -> None:
        src = Path(os.fsdecode(event.src_path))
        if src.suffix in (".py", ".json") and not src.name.startswith("."):
            logger.info("Plugin file modified", file=str(src))
            self._trigger_reload(src.parent)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            src_str = os.fsdecode(event.src_path)
            norm_path = str(Path(src_str).resolve())
            folder_name = Path(src_str).name
            logger.info("Plugin directory deleted", path=src_str, folder=folder_name)
            self._trigger_unload_by_path(norm_path, folder_name)

    def _trigger_reload(self, target_dir: Path) -> None:
        async def _do_reload() -> None:
            try:
                norm_path = str(target_dir.resolve())
                plugins = self.loader.load_from_directory(target_dir)
                loaded_names: set[str] = set()
                for plugin in plugins:
                    await self.lifecycle.reload(plugin)
                    loaded_names.add(plugin.name)
                if loaded_names:
                    self._dir_to_plugins[norm_path] = loaded_names
                logger.info("Hot-reload completed", count=len(plugins), path=norm_path)
            except Exception as e:
                logger.error("Hot-reload failed", error=str(e))

        asyncio.run_coroutine_threadsafe(_do_reload(), self.loop)

    def _trigger_unload_by_path(self, norm_path: str, folder_name: str) -> None:
        async def _do_unload() -> None:
            try:
                plugin_names = set(self._dir_to_plugins.pop(norm_path, set()))
                if folder_name in self.lifecycle.plugins:
                    plugin_names.add(folder_name)
                for registered_name, entry in list(self.lifecycle.plugins.items()):
                    plugin_root = getattr(entry.plugin, "root", None)
                    if plugin_root and str(Path(plugin_root).resolve()) == norm_path:
                        plugin_names.add(registered_name)

                for name in plugin_names:
                    if name in self.lifecycle.plugins:
                        await self.lifecycle.unload(name)
                        logger.info("Plugin unloaded via watcher", plugin=name)
            except Exception as e:
                logger.error("Unload failed", error=str(e))

        asyncio.run_coroutine_threadsafe(_do_unload(), self.loop)


class PluginWatcher:
    """Watches directories and coordinates live plugin hot-reloading."""

    def __init__(
        self,
        plugin_dirs: list[Path],
        loader: PluginLoader,
        lifecycle: PluginLifecycle,
    ) -> None:
        self.plugin_dirs = plugin_dirs
        self.loader = loader
        self.lifecycle = lifecycle
        self._observer: Any = None

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Start the watchdog observer."""
        if loop is not None:
            current_loop = loop
        else:
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                current_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(current_loop)

        handler = PluginFileEventHandler(self.loader, self.lifecycle, current_loop)

        self._observer = Observer()
        for pdir in self.plugin_dirs:
            if pdir.exists():
                self._observer.schedule(handler, str(pdir), recursive=True)
                logger.info("Watching plugin directory for hot-reload", directory=str(pdir))

        self._observer.start()

    def stop(self) -> None:
        """Stop the watchdog observer."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Plugin watcher stopped")


@dataclass(slots=True, frozen=True)
class CommentTrigger:
    """Represents a discovered autonomous agent comment marker in code."""

    file_path: str
    line_number: int
    marker: str
    instruction: str


_TRIGGER_PATTERNS = [
    re.compile(r"(?:#|//|/\*)\s*(?:HARNESS|AI):\s*(.+?)(?:\*/)?$", re.IGNORECASE),
]


def scan_file_for_triggers(file_path: Path | str) -> list[CommentTrigger]:
    """Scan a source file for autonomous comment instruction triggers."""
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return []

    triggers: list[CommentTrigger] = []
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for idx, line in enumerate(lines, start=1):
            for pat in _TRIGGER_PATTERNS:
                m = pat.search(line)
                if m:
                    instruction = m.group(1).strip()
                    triggers.append(
                        CommentTrigger(
                            file_path=str(p).replace("\\", "/"),
                            line_number=idx,
                            marker="HARNESS",
                            instruction=instruction,
                        )
                    )
    except Exception as err:
        logger.debug("scan_trigger_failed", path=str(p), error=str(err))

    return triggers


class CommentTriggerEventHandler(FileSystemEventHandler):
    """Watches source directory and notifies on discovered autonomous triggers."""

    def __init__(self, callback: Callable[[CommentTrigger], Any], loop: asyncio.AbstractEventLoop) -> None:
        self.callback = callback
        self.loop = loop

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        p = Path(os.fsdecode(event.src_path))
        if p.suffix in (".py", ".ts", ".js", ".rs", ".go", ".md"):
            triggers = scan_file_for_triggers(p)
            for trig in triggers:
                if asyncio.iscoroutinefunction(self.callback):
                    asyncio.run_coroutine_threadsafe(self.callback(trig), self.loop)
                else:
                    self.callback(trig)


class CommentTriggerWatcher:
    """Watches workspace files for comment instruction triggers (# HARNESS: ...)."""

    def __init__(self, watch_path: Path | str, callback: Callable[[CommentTrigger], Any]) -> None:
        self.watch_path = Path(watch_path)
        self.callback = callback
        self._observer: Any = None

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        current_loop = loop or asyncio.get_event_loop()
        handler = CommentTriggerEventHandler(self.callback, current_loop)
        self._observer = Observer()
        if self.watch_path.exists():
            self._observer.schedule(handler, str(self.watch_path), recursive=True)
            self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None


__all__ = [
    "CommentTrigger",
    "CommentTriggerWatcher",
    "PluginFileEventHandler",
    "PluginWatcher",
    "scan_file_for_triggers",
]
