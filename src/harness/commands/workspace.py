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

    p_dirs = [Path(p) for p in (plugin_dirs or [Path("plugins")])]
    rt = runtime or HarnessRuntime.create(plugin_dirs=p_dirs)
    if not runtime:
        await rt.start()

    watcher = PluginWatcher(plugin_dirs=p_dirs, runtime=rt)
    watcher.start()

    logger.info("Started workspace watcher", plugin_dirs=[str(p) for p in p_dirs])

    if shutdown_event:
        await shutdown_event.wait()
        watcher.stop()
        if not runtime:
            await rt.stop()

    return watcher


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.command("init")
@click.argument("path", default=".", type=click.Path())
def init_cli(path: str) -> None:
    """Initialize a harness workspace."""
    res = init_workspace_cmd(path)
    click.echo(f"✓ Workspace initialized at {res.workspace_path}")
    click.echo("  plugins/          → Drop-in plugin directory")
    click.echo("  .harness/         → Configuration and data")
    click.echo("\nNext: harness plugin add <github-url>")


@click.command("watch")
def watch_cli() -> None:
    """Run the harness with live filesystem hot-reloading enabled."""

    async def _watch() -> None:
        from harness.kernel.runtime import HarnessRuntime

        runtime = HarnessRuntime.create(db_path=":memory:")
        await runtime.start()

        watcher = await watch_workspace_cmd(
            plugin_dirs=[Path("plugins")],
            runtime=runtime,
        )

        click.echo("👁️  Harness Watcher active. Monitoring plugins/ for live hot-reload...")
        click.echo("Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            watcher.stop()
            await runtime.stop()
            click.echo("\n✓ Watcher stopped.")

    try:
        _run_async(_watch())
    except KeyboardInterrupt:
        pass


__all__ = [
    "WorkspaceInitResult",
    "init_cli",
    "init_workspace_cmd",
    "watch_cli",
    "watch_workspace_cmd",
]
