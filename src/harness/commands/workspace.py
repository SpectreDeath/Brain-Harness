"""Workspace commands — pure async functions for workspace lifecycle and hot-reloading."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from harness.kernel.runtime import HarnessRuntime
    from harness.plugins.watcher import PluginWatcher

logger = structlog.get_logger()


@dataclass
class WorkspaceInitResult:
    """Outcome of initializing a Harness workspace."""

    workspace_path: Path
    plugins_dir: Path
    config_dir: Path
    config_file: Path
    created_files: list[Path] = field(default_factory=list)
    status: str = "initialized"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_path": str(self.workspace_path),
            "plugins_dir": str(self.plugins_dir),
            "config_dir": str(self.config_dir),
            "config_file": str(self.config_file),
            "created_files": [str(p) for p in self.created_files],
            "status": self.status,
        }


def init_workspace_cmd(path: str | Path = ".") -> WorkspaceInitResult:
    """Initialize a Harness workspace on the local filesystem.

    Creates ``plugins/`` and ``.harness/`` directories and a default ``config.json``.

    Args:
        path: Root path of the workspace to initialize (default current working directory).

    Returns:
        WorkspaceInitResult containing created directories and files.
    """
    workspace = Path(path).resolve()
    plugins_dir = workspace / "plugins"
    config_dir = workspace / ".harness"
    config_file = config_dir / "config.json"

    plugins_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []
    if not config_file.exists():
        config = {
            "version": "0.1.0",
            "plugin_dirs": ["plugins"],
            "event_log": ".harness/events.jsonl",
            "storage_db": ".harness/storage.db",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        created_files.append(config_file)

    logger.info("Initialized Harness workspace", workspace=str(workspace))
    return WorkspaceInitResult(
        workspace_path=workspace,
        plugins_dir=plugins_dir,
        config_dir=config_dir,
        config_file=config_file,
        created_files=created_files,
        status="initialized",
    )


async def watch_workspace_cmd(
    plugin_dirs: list[Path | str] | None = None,
    runtime: HarnessRuntime | None = None,
    shutdown_event: asyncio.Event | None = None,
    poll_interval: float = 1.0,
) -> PluginWatcher:
    """Start the filesystem watcher for live hot-reloading.

    Args:
        plugin_dirs: Directories to monitor for plugin changes.
        runtime: Active HarnessRuntime instance. If None, one is created.
        shutdown_event: Optional asyncio.Event to trigger graceful shutdown.
        poll_interval: Sleep interval when blocking.

    Returns:
        Running PluginWatcher instance.
    """
    from harness.kernel.runtime import HarnessRuntime
    from harness.plugins.watcher import PluginWatcher

    dirs = [Path(d).resolve() for d in (plugin_dirs or [Path("plugins")])]
    rt = runtime or HarnessRuntime.create(db_path=":memory:")
    if not runtime:
        await rt.start()

    watcher = PluginWatcher(dirs, rt.loader, rt.lifecycle)
    watcher.start()
    logger.info("Started workspace plugin watcher", directories=[str(d) for d in dirs])

    if shutdown_event:
        try:
            await shutdown_event.wait()
        finally:
            watcher.stop()
            if not runtime:
                await rt.stop()
            logger.info("Stopped workspace plugin watcher")

    return watcher


__all__ = [
    "WorkspaceInitResult",
    "init_workspace_cmd",
    "watch_workspace_cmd",
]
