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
    include_sandboxed: bool = False,
) -> dict[str, bool]:
    """Enable all plugins on a running runtime or new instance."""
    if runtime is not None:
        try:
            results = await runtime.enable_all_plugins(include_sandboxed=include_sandboxed)
        except TypeError:
            results = await runtime.enable_all_plugins()
        enabled = [p for p, ok in results.items() if ok]
        if enabled:
            _update_persistent_config(enabled=enabled, config_dir=config_dir)
        return cast(dict[str, bool], results)


    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path) as rt:
        results = await rt.enable_all_plugins(include_sandboxed=include_sandboxed)
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


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.group("plugin")
def plugin_group() -> None:
    """Manage plugins."""


@plugin_group.command("add")
@click.argument("source")
@click.option("--ref", default="main", help="Git ref (branch/tag) to fetch")
@click.option("--force", is_flag=True, help="Re-download even if cached")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
def plugin_add(source: str, ref: str, force: bool, token: str | None) -> None:
    """Fetch a GitHub repository and register it as a plugin.

    SOURCE can be a GitHub URL, owner/repo shorthand, or local ZIP path.
    """
    click.echo(f"⟳ Ingesting plugin from {source}...")
    plugin, manifest = _run_async(add_plugin(source, ref=ref, force=force, token=token))

    if manifest:
        click.echo(f"  ✓ Manifest: {manifest.name}@{manifest.version}")
        click.echo(f"    Language:    {manifest.language}")
        click.echo(f"    Entrypoint:  {manifest.entrypoint or '(auto-detect)'}")
        click.echo(f"    Isolation:   {manifest.isolation.value}")
        click.echo(f"    Entrypoints: {len(manifest.entrypoints)} functions found")

        if manifest.dependencies:
            click.echo(f"    Dependencies: {', '.join(manifest.dependencies[:5])}")
            if len(manifest.dependencies) > 5:
                click.echo(f"      ... and {len(manifest.dependencies) - 5} more")

    click.echo(f"\n✓ Plugin '{plugin.name}' added successfully!")
    click.echo("  Run 'harness plugin list' to see all plugins")


@plugin_group.command("list")
def plugin_list() -> None:
    """List all installed plugins."""
    cached = list_plugins()

    if not cached:
        click.echo("No plugins installed.")
        click.echo("Run 'harness plugin add <github-url>' to add one.")
        return

    click.echo(f"{'Name':<30} {'Manifest':<12} {'Path'}")
    click.echo("─" * 80)
    for entry in cached:
        has_manifest = "✓" if entry["has_manifest"] else "✗"
        click.echo(f"{entry['name']:<30} {has_manifest:<12} {entry['path']}")

    click.echo(f"\nTotal: {len(cached)} plugin(s)")


@plugin_group.command("remove")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to remove this plugin?")
def plugin_remove(name: str) -> None:
    """Remove a cached plugin."""
    if remove_plugin(name):
        click.echo(f"✓ Removed plugin '{name}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin_group.command("inspect")
@click.argument("source")
def plugin_inspect(source: str) -> None:
    """Inspect a plugin directory and show its manifest card."""
    try:
        manifest = inspect_plugin(source)
    except FileNotFoundError:
        click.echo(f"✗ Not found: {source}")
        return

    click.echo(manifest.format_card())


@plugin_group.command("info")
@click.argument("name")
def plugin_info(name: str) -> None:
    """Show the standardized summary card for an installed plugin."""
    manifest = get_plugin_manifest(name)
    if not manifest:
        click.echo(f"✗ Plugin '{name}' not found")
        return

    click.echo(manifest.format_card())
    if manifest.entrypoints:
        click.echo("\nSample Skills / Tools:")
        for ep in manifest.entrypoints[:10]:
            params = ", ".join(p.name for p in ep.parameters)
            click.echo(f"  * {ep.name}({params})")
            if ep.description:
                click.echo(f"      {ep.description[:80]}")
    click.echo("\nRun 'harness plugin guide " + name + "' to view the Quick Start Guide")


@plugin_group.command("card")
@click.argument("name")
def plugin_card(name: str) -> None:
    """Show the standardized summary card for an installed plugin."""
    manifest = get_plugin_manifest(name)
    if not manifest:
        click.echo(f"✗ Plugin '{name}' not found")
        return
    click.echo(manifest.format_card())


@plugin_group.command("guide")
@click.argument("name")
def plugin_guide(name: str) -> None:
    """Show the Quick Start and Agent Usage Guide for an installed plugin."""
    result = get_plugin_guide(name)
    if not result:
        click.echo(f"✗ Plugin '{name}' not found")
        return

    manifest, guide = result
    click.echo(guide)


@plugin_group.command("enable")
@click.argument("name")
def plugin_enable(name: str) -> None:
    """Enable a plugin by name or pattern."""
    matched = _run_async(enable_plugin_by_name(name))
    if matched:
        for pname in matched:
            click.echo(f"✓ Enabled plugin '{pname}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin_group.command("disable")
@click.argument("name")
def plugin_disable(name: str) -> None:
    """Disable a plugin by name or pattern."""
    matched = _run_async(disable_plugin_by_name(name))
    if matched:
        for pname in matched:
            click.echo(f"✓ Disabled plugin '{pname}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin_group.command("enable-all")
def plugin_enable_all() -> None:
    """Enable all discovered plugins."""
    results = _run_async(enable_all_plugins())
    click.echo(f"✓ Enabled {sum(results.values())}/{len(results)} plugins")


@plugin_group.command("disable-all")
@click.option("--keep-core/--all", default=True, help="Keep core infrastructure services active")
def plugin_disable_all(keep_core: bool) -> None:
    """Disable all active plugins."""
    disabled = _run_async(disable_all_plugins(keep_core=keep_core))
    click.echo(f"✓ Disabled {len(disabled)} plugins")


__all__ = [
    "add_plugin",
    "disable_all_plugins",
    "disable_plugin",
    "disable_plugin_by_name",
    "enable_all_plugins",
    "enable_plugin",
    "enable_plugin_by_name",
    "get_plugin_guide",
    "get_plugin_manifest",
    "inspect_plugin",
    "list_plugins",
    "plugin_group",
    "remove_plugin",
]


