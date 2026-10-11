"""Plugin ingestion and batch lifecycle coordination for Harness Runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
import structlog

from harness.kernel.lifecycle import PluginState

if TYPE_CHECKING:
    from harness.kernel.runtime.coordinator import HarnessRuntime
    from harness.plugins.base import HarnessPlugin

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)


async def ingest_plugin_from_source(
    runtime: HarnessRuntime,
    source: str | Path,
    *,
    ref: str = "main",
    force: bool = False,
    token: str | None = None,
    auto_enable: bool = True,
) -> HarnessPlugin:
    """Ingest a plugin from GitHub URL, ZIP archive, or local path and register it."""
    from harness.ingestion.pipeline import PluginIngestionPipeline

    pipeline = PluginIngestionPipeline(
        plugin_dir=runtime._plugin_dirs[0] if runtime._plugin_dirs else None,
        github_token=token,
    )
    plugin = await pipeline.ingest(str(source), ref=ref, force=force)
    runtime.register_plugin(plugin)

    if runtime.is_running and auto_enable:
        await runtime.lifecycle.ensure_enabled(plugin.name)

    return plugin


async def enable_all_plugins(
    runtime: HarnessRuntime,
    *,
    include_sandboxed: bool = False,
) -> dict[str, bool]:
    """Enable all discovered and validated plugins."""
    return await runtime.lifecycle.enable_all(
        trusted_only=not include_sandboxed,
        skip_user_plugins=not include_sandboxed,
    )


async def disable_all_plugins(
    runtime: HarnessRuntime,
    *,
    keep_core: bool = True,
) -> list[str]:
    """Disable all active plugins.

    Args:
        runtime: Target Harness runtime instance.
        keep_core: If True, keeps core services (tools, storage, llm) running.
    """
    core_plugins = {"tools.registry", "storage.sqlite", "llm.provider"} if keep_core else set()
    disabled: list[str] = []
    for name, entry in list(runtime.lifecycle.plugins.items()):
        if entry.state == PluginState.ENABLED and name not in core_plugins:
            try:
                await runtime.lifecycle.disable(name)
                disabled.append(name)
            except Exception as e:
                logger.warning("Failed disabling plugin", plugin=name, error=str(e))
    return disabled


__all__ = [
    "disable_all_plugins",
    "enable_all_plugins",
    "ingest_plugin_from_source",
]
