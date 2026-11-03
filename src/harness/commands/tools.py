"""Tool commands — pure async functions for granular tool/skill management."""

from __future__ import annotations

from typing import Any
import json
from pathlib import Path
import structlog

logger = structlog.get_logger()


def _update_persistent_tool_state(
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
    config_dir: Path | None = None,
) -> None:
    """Persist enabled/disabled tool changes to .harness/tool_state.json if directory exists."""
    target_dir = config_dir or Path(".harness")
    if not target_dir.exists():
        return

    state_file = target_dir / "tool_state.json"
    data: dict[str, Any] = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    enabled_set = set(data.get("enabled_tools", []))
    disabled_set = set(data.get("disabled_tools", []))

    if enabled:
        for t in enabled:
            enabled_set.add(t)
            disabled_set.discard(t)

    if disabled:
        for t in disabled:
            disabled_set.add(t)
            enabled_set.discard(t)

    data["enabled_tools"] = sorted(enabled_set)
    data["disabled_tools"] = sorted(disabled_set)

    try:
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug("Failed to persist tool state updates", error=str(e))


def list_tools(
    registry: Any,
    *,
    provider: str | None = None,
    enabled_only: bool = False,
) -> list[dict[str, Any]]:
    """List tools from the tool registry with details."""
    if registry is None:
        return []

    tools = registry.list_tools(enabled_only=enabled_only, provider=provider)
    return [
        {
            "name": t.name,
            "description": t.description,
            "provider": t.provider,
            "enabled": t.enabled,
            "parameters": list(t.parameters_schema.get("properties", {}).keys())
            if t.parameters_schema
            else [],
        }
        for t in tools
    ]


def enable_tool(registry: Any, name: str) -> bool:
    """Enable a specific tool in the registry."""
    if registry is not None:
        return bool(registry.enable_tool(name))
    return False


def disable_tool(registry: Any, name: str) -> bool:
    """Disable a specific tool in the registry."""
    if registry is not None:
        return bool(registry.disable_tool(name))
    return False


def toggle_tool(registry: Any, name: str, enabled: bool | None = None) -> bool:
    """Toggle a specific tool in the registry."""
    if registry is not None:
        return bool(registry.toggle_tool(name, enabled=enabled))
    return False


async def list_tools_summary(
    *,
    provider: str | None = None,
    enabled_only: bool = False,
    db_path: str = ":memory:",
) -> list[dict[str, Any]]:
    """Standalone async command to list tools across a runtime instance."""
    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path) as rt:
        if rt.tools is None:
            return []
        return list_tools(rt.tools, provider=provider, enabled_only=enabled_only)


async def toggle_tool_by_name(
    name: str,
    enabled: bool | None = None,
    *,
    db_path: str = ":memory:",
    exact: bool = True,
) -> list[str]:
    """Standalone async command to toggle tool(s) matching exact name or declared alias."""
    from harness.kernel.runtime import HarnessRuntime

    matched: list[str] = []
    async with HarnessRuntime.create(db_path=db_path) as rt:
        if rt.tools is None:
            return []

        target = rt.tools.resolve_tool_name(name)
        if rt.tools.has_tool(target):
            rt.tools.toggle_tool(target, enabled=enabled)
            matched.append(target)
        elif not exact:
            # Fallback substring matching only if non-exact pattern matching is requested
            for t in rt.tools.list_tools():
                if name in t.name:
                    rt.tools.toggle_tool(t.name, enabled=enabled)
                    matched.append(t.name)

    if matched:
        if enabled is True:
            _update_persistent_tool_state(enabled=matched)
        elif enabled is False:
            _update_persistent_tool_state(disabled=matched)

    return matched


async def enable_tool_by_name(
    name: str,
    *,
    db_path: str = ":memory:",
) -> list[str]:
    """Standalone async command to enable tool(s) matching a name or pattern."""
    return await toggle_tool_by_name(name, enabled=True, db_path=db_path)


async def disable_tool_by_name(
    name: str,
    *,
    db_path: str = ":memory:",
) -> list[str]:
    """Standalone async command to disable tool(s) matching a name or pattern."""
    return await toggle_tool_by_name(name, enabled=False, db_path=db_path)


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.group("tool")
def tool_group() -> None:
    """Inspect and manage granular tool and skill enablement."""


@tool_group.command("list")
@click.option("--provider", help="Filter tools by provider plugin name")
@click.option("--enabled-only", is_flag=True, help="Only list currently enabled tools")
def tool_list(provider: str | None, enabled_only: bool) -> None:
    """List all registered tools with their active status."""
    tools = _run_async(list_tools_summary(provider=provider, enabled_only=enabled_only))
    if not tools:
        click.echo("No tools found.")
        return

    click.echo(f"{'Tool Name':<38} {'Status':<10} {'Provider'}")
    click.echo("─" * 75)
    for t in tools:
        status_str = "✓ Enabled" if t["enabled"] else "✗ Disabled"
        click.echo(f"{t['name']:<38} {status_str:<10} {t['provider']}")
    click.echo(f"\nTotal: {len(tools)} tool(s)")


@tool_group.command("enable")
@click.argument("name")
def tool_enable(name: str) -> None:
    """Enable a specific tool by name."""
    matched = _run_async(enable_tool_by_name(name))
    if matched:
        for tname in matched:
            click.echo(f"✓ Enabled tool '{tname}'")
    else:
        click.echo(f"✗ Tool '{name}' not found")


@tool_group.command("disable")
@click.argument("name")
def tool_disable(name: str) -> None:
    """Disable a specific tool by name."""
    matched = _run_async(disable_tool_by_name(name))
    if matched:
        for tname in matched:
            click.echo(f"✓ Disabled tool '{tname}'")
    else:
        click.echo(f"✗ Tool '{name}' not found")


__all__ = [
    "disable_tool",
    "disable_tool_by_name",
    "enable_tool",
    "enable_tool_by_name",
    "list_tools",
    "list_tools_summary",
    "toggle_tool",
    "toggle_tool_by_name",
    "tool_group",
]

