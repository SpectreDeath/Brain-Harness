"""Plugin commands — pure async functions for plugin management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import structlog

from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.plugins.base import HarnessPlugin
from harness.plugins.loader import PluginLoader
from harness.plugins.manifest import PluginManifest

logger = structlog.get_logger()


def _update_persistent_config(
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
    config_dir: Path | None = None,
) -> None:
    """Persist enabled/disabled plugin changes to .harness/config.json if directory exists."""
    target_dir = config_dir or Path(".harness")
    if not target_dir.exists():
        return

    config_file = target_dir / "config.json"
    data: dict[str, Any] = {}
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    enabled_set = set(data.get("enabled_plugins", []))
    disabled_set = set(data.get("disabled_plugins", []))

    if enabled:
        for p in enabled:
            enabled_set.add(p)
            disabled_set.discard(p)

    if disabled:
        for p in disabled:
            disabled_set.add(p)
            enabled_set.discard(p)

    data["enabled_plugins"] = sorted(enabled_set)
    data["disabled_plugins"] = sorted(disabled_set)

    try:
        config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug("Failed to persist plugin config updates", error=str(e))


async def add_plugin(
    source: str,
    *,
    ref: str = "main",
    force: bool = False,
    token: str | None = None,
    plugin_dir: Path | None = None,
) -> tuple[HarnessPlugin, PluginManifest | None]:
    """Ingest a plugin from GitHub URL or ZIP archive and return the plugin and manifest."""
    pipeline = PluginIngestionPipeline(plugin_dir=plugin_dir, github_token=token)
    plugin = await pipeline.ingest(source, ref=ref, force=force)
    manifest = getattr(plugin, "manifest", None)
    return plugin, manifest


def list_plugins(plugin_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all installed and cached plugins via the catalog seam."""
    p_dirs = [plugin_dir] if plugin_dir else [Path("plugins")]
    loader = PluginLoader(plugin_dirs=p_dirs)
    return loader.list_catalog()


def inspect_plugin(source: str | Path, plugin_dir: Path | None = None) -> PluginManifest:
    """Inspect a plugin directory or archive and return its manifest."""
    p_dirs = [plugin_dir] if plugin_dir else [Path("plugins")]
    loader = PluginLoader(plugin_dirs=p_dirs)
    manifest = loader.get_manifest(str(source))
    if manifest is not None:
        return manifest

    pipeline = PluginIngestionPipeline(plugin_dir=plugin_dir)
    return pipeline.inspect(source)


def get_plugin_manifest(name: str, plugin_dir: Path | None = None) -> PluginManifest | None:
    """Find and return the manifest for an installed plugin."""
    p_dirs = [plugin_dir] if plugin_dir else [Path("plugins")]
    loader = PluginLoader(plugin_dirs=p_dirs)
    return loader.get_manifest(name)


def get_plugin_guide(name: str, plugin_dir: Path | None = None) -> tuple[PluginManifest, str] | None:
    """Return the manifest and formatted Quick Start Guide for a plugin."""
    p_dirs = [plugin_dir] if plugin_dir else [Path("plugins")]
    loader = PluginLoader(plugin_dirs=p_dirs)
    return loader.get_guide(name)


def remove_plugin(name: str, plugin_dir: Path | None = None) -> bool:
    """Remove a cached plugin by name."""
    pipeline = PluginIngestionPipeline(plugin_dir=plugin_dir)
    return pipeline.remove_cached(name)


async def enable_plugin(
    name: str,
    *,
    runtime: Any | None = None,
    plugin_dirs: list[Path] | None = None,
) -> bool:
    """Enable a plugin on a running runtime or standalone lifecycle."""
    if runtime is not None:
        success = await runtime.enable_plugin(name)
        if success:
            _update_persistent_config(enabled=[name])
        return bool(success)
    return False


async def disable_plugin(
    name: str,
    *,
    runtime: Any | None = None,
) -> bool:
    """Disable a plugin on a running runtime."""
    if runtime is not None:
        success = await runtime.disable_plugin(name)
        if success:
            _update_persistent_config(disabled=[name])
        return bool(success)
    return False


async def enable_plugin_by_name(
    name: str,
    *,
    db_path: str = ":memory:",
    runtime: Any | None = None,
    config_dir: Path | None = None,
) -> list[str]:
    """Enable plugin(s) matching a name or pattern."""
    if runtime is not None:
        matched: list[str] = []
        for pname in list(runtime.lifecycle.plugins.keys()):
            if pname == name or name in pname:
                success = await runtime.enable_plugin(pname)
                if success:
                    matched.append(pname)
        if matched:
            _update_persistent_config(enabled=matched, config_dir=config_dir)
        return matched

    from harness.kernel.runtime import HarnessRuntime

    matched = []
    async with HarnessRuntime.create(db_path=db_path) as rt:
        for pname in list(rt.lifecycle.plugins.keys()):
            if pname == name or name in pname:
                success = await rt.enable_plugin(pname)
                if success:
                    matched.append(pname)
    if matched:
        _update_persistent_config(enabled=matched, config_dir=config_dir)
    return matched


async def disable_plugin_by_name(
    name: str,
    *,
    db_path: str = ":memory:",
    runtime: Any | None = None,
    config_dir: Path | None = None,
) -> list[str]:
    """Disable plugin(s) matching a name or pattern."""
    if runtime is not None:
        matched: list[str] = []
        for pname in list(runtime.lifecycle.plugins.keys()):
            if pname == name or name in pname:
                success = await runtime.disable_plugin(pname)
                if success:
                    matched.append(pname)
        if matched:
            _update_persistent_config(disabled=matched, config_dir=config_dir)
        return matched

    from harness.kernel.runtime import HarnessRuntime

    matched = []
    async with HarnessRuntime.create(db_path=db_path) as rt:
        for pname in list(rt.lifecycle.plugins.keys()):
            if pname == name or name in pname:
                success = await rt.disable_plugin(pname)
                if success:
                    matched.append(pname)
    if matched:
        _update_persistent_config(disabled=matched, config_dir=config_dir)
    return matched


async def enable_all_plugins(
    *,
    runtime: Any | None = None,
    db_path: str = ":memory:",
    config_dir: Path | None = None,
) -> dict[str, bool]:
    """Enable all plugins on a running runtime or new instance."""
    if runtime is not None:
        results = await runtime.enable_all_plugins()
        enabled = [p for p, ok in results.items() if ok]
        if enabled:
            _update_persistent_config(enabled=enabled, config_dir=config_dir)
        return cast(dict[str, bool], results)

    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path) as rt:
        results = await rt.enable_all_plugins()
        enabled = [p for p, ok in results.items() if ok]
        if enabled:
            _update_persistent_config(enabled=enabled, config_dir=config_dir)
        return cast(dict[str, bool], results)


async def disable_all_plugins(
    *,
    runtime: Any | None = None,
    keep_core: bool = True,
    db_path: str = ":memory:",
    config_dir: Path | None = None,
) -> list[str]:
    """Disable all plugins on a running runtime or new instance."""
    if runtime is not None:
        disabled = await runtime.disable_all_plugins(keep_core=keep_core)
        if disabled:
            _update_persistent_config(disabled=disabled, config_dir=config_dir)
        return cast(list[str], disabled)

    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path) as rt:
        disabled = await rt.disable_all_plugins(keep_core=keep_core)
        if disabled:
            _update_persistent_config(disabled=disabled, config_dir=config_dir)
        return cast(list[str], disabled)


