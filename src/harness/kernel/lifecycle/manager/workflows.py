"""Atomic multi-step transitions and hot-reload workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.lifecycle.models import (
    PluginEntry,
    PluginState,
)

if TYPE_CHECKING:
    from harness.kernel.lifecycle.manager.core import PluginLifecycle
    from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


async def ensure_enabled(
    manager: PluginLifecycle, entries: dict[str, PluginEntry], name: str
) -> bool:
    """Advance a plugin from its current state directly to ENABLED."""
    entry = entries.get(name)
    if entry is None:
        raise KeyError(f"Plugin not found: {name!r}")

    if entry.state == PluginState.ENABLED:
        return True

    try:
        if entry.state == PluginState.ERROR:
            manager._transition(name, PluginState.DISCOVERED)

        if entry.state in (PluginState.DISCOVERED, PluginState.UNLOADED):
            if entry.state == PluginState.UNLOADED:
                manager.discover(entry.plugin)
            await manager.load(name)

        if entry.state == PluginState.LOADED:
            await manager.validate(name)

        if entry.state in (PluginState.VALIDATED, PluginState.DISABLED):
            await manager.enable(name)

        return entry.state == PluginState.ENABLED
    except Exception as e:
        logger.error("ensure_enabled failed", plugin=name, error=str(e))
        return False


async def register_and_enable(
    manager: PluginLifecycle, plugin: HarnessPlugin
) -> bool:
    """Atomically register, load, validate, and enable a plugin in one call."""
    manager.discover(plugin)
    return await manager.ensure_enabled(plugin.name)


async def reload_plugin(
    manager: PluginLifecycle, entries: dict[str, PluginEntry], plugin: HarnessPlugin
) -> bool:
    """Atomically reload or hot-swap an active or modified plugin instance."""
    name = plugin.name
    if name in entries:
        entry = entries[name]
        if entry.state in (
            PluginState.LOADED,
            PluginState.VALIDATED,
            PluginState.ENABLED,
            PluginState.DISABLED,
        ):
            try:
                await manager.unload(name)
            except Exception as e:
                logger.warning(
                    "Unload during plugin reload encountered warning",
                    plugin=name,
                    error=str(e),
                )

    manager.discover(plugin)
    return await manager.ensure_enabled(name)
