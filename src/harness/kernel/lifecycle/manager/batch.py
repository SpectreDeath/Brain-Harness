"""Batch lifecycle operations and wave scheduling."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.graph import CyclicDependencyError
from harness.kernel.lifecycle.models import (
    PluginEntry,
    PluginState,
)

if TYPE_CHECKING:
    from harness.kernel.lifecycle.manager.core import PluginLifecycle

logger = structlog.get_logger()


async def enable_all_plugins(
    manager: PluginLifecycle,
    context: Any,
    entries: dict[str, PluginEntry],
    trusted_only: bool = False,
    skip_user_plugins: bool = False,
    enable_timeout: float = 30.0,
) -> dict[str, bool]:
    """Enable all discovered and validated plugins in topological dependency order."""
    for name, entry in list(entries.items()):
        is_user = name.startswith("plugin.")
        if skip_user_plugins and is_user:
            continue
        if trusted_only and not entry.plugin.trusted:
            continue
        if entry.state == PluginState.DISCOVERED:
            try:
                await manager.load(name)
                await manager.validate(name)
            except Exception as e:
                logger.warning(
                    "Failed loading plugin before enable_all",
                    plugin=name,
                    error=str(e),
                )
        elif entry.state == PluginState.LOADED:
            try:
                await manager.validate(name)
            except Exception as e:
                logger.warning(
                    "Failed validating plugin before enable_all",
                    plugin=name,
                    error=str(e),
                )

    to_enable = [
        n
        for n, e in entries.items()
        if e.state in (PluginState.VALIDATED, PluginState.DISABLED)
        and (not trusted_only or e.plugin.trusted)
        and (not skip_user_plugins or not n.startswith("plugin."))
    ]

    try:
        waves = manager.resolve_enable_waves(to_enable)
    except CyclicDependencyError:
        logger.error("Cannot enable plugins: cyclic dependencies detected")
        raise

    results: dict[str, bool] = {
        n: True for n, e in entries.items() if e.state == PluginState.ENABLED
    }
    failed_names: set[str] = set()
    graph = manager.build_dependency_graph(to_enable)

    for wave in waves:
        runnable: list[str] = []
        for name in wave:
            if any(dep in failed_names for dep in graph.transitive_dependencies(name)):
                failed_names.add(name)
                results[name] = False
                entry = entries.get(name)
                if entry and entry.state != PluginState.ERROR:
                    entry.state = PluginState.ERROR
                    entry.error = "Prerequisite plugin failure in dependencies"
            else:
                runnable.append(name)

        if not runnable:
            continue

        wave_results = await asyncio.gather(
            *[
                asyncio.wait_for(manager.enable(n), timeout=enable_timeout)
                for n in runnable
            ],
            return_exceptions=True,
        )

        for name, res in zip(runnable, wave_results):
            if isinstance(res, Exception):
                failed_names.add(name)
                results[name] = False
                entry = entries.get(name)
                if entry and entry.state != PluginState.ERROR:
                    entry.state = PluginState.ERROR
                    entry.error = str(res) or f"Timed out after {enable_timeout}s"
                context.set_plugin_services_active(name, False)
                logger.error(
                    "Failed to enable plugin in wave", plugin=name, error=str(res)
                )
            else:
                results[name] = True

    return results


async def disable_all_plugins(
    manager: PluginLifecycle, entries: dict[str, PluginEntry]
) -> dict[str, bool]:
    """Disable all enabled plugins in reverse dependency order."""
    enabled = [
        n for n, e in entries.items() if e.state == PluginState.ENABLED
    ]

    try:
        order = manager.resolve_enable_order(enabled)
    except CyclicDependencyError:
        order = enabled

    results: dict[str, bool] = {}
    for name in reversed(order):
        try:
            await manager.disable(name)
            results[name] = True
        except Exception as e:
            results[name] = False
            logger.error("Failed to disable plugin", plugin=name, error=str(e))

    return results


async def unload_all_plugins(
    manager: PluginLifecycle, entries: dict[str, PluginEntry]
) -> dict[str, bool]:
    """Unload all plugins, disabling them first if needed."""
    await manager.disable_all()

    results: dict[str, bool] = {}
    for name, entry in list(entries.items()):
        if entry.state in (
            PluginState.DISABLED,
            PluginState.LOADED,
            PluginState.VALIDATED,
        ):
            try:
                await manager.unload(name)
                results[name] = True
            except Exception as e:
                results[name] = False
                logger.error("Failed to unload plugin", plugin=name, error=str(e))

    return results
