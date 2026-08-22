"""Tool commands — pure async functions for granular tool/skill management."""

from __future__ import annotations

from typing import Any


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
) -> list[str]:
    """Standalone async command to toggle tool(s) matching a name or pattern."""
    from harness.kernel.runtime import HarnessRuntime

    matched: list[str] = []
    async with HarnessRuntime.create(db_path=db_path) as rt:
        if rt.tools is None:
            return []
        for t in rt.tools.list_tools():
            if t.name == name or name in t.name:
                rt.toggle_tool(t.name, enabled=enabled)
                matched.append(t.name)
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

