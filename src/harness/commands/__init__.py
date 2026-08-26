"""Harness commands — pure async entry points for every CLI action and headless engine.

Each function here is a plain ``async def`` (or sync where pure data mapping) and can be called by:
- The Click CLI adapters in ``harness.cli``
- The web UI server (``harness.ui``)
- External Model Context Protocol (MCP) clients
- Autonomous agent swarms
- In-memory test fixtures (no CliRunner or subprocess required)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import inspect
import time
from typing import Any, Callable

import structlog

from .agent import FallbackLLM, run_agent
from .bridges import (
    check_bridge_status_cmd,
    list_bridges_cmd,
)
from .compute import (
    ComputeAssessmentResult,
    assess_compute_cmd,
)
from .creator import (
    build_plugin_cmd,
    list_archetypes_cmd,
    remediate_plugin_cmd,
    scaffold_plugin_cmd,
    validate_plugin_cmd,
)
from .events import (
    EventQueryResult,
    get_events_cmd,
)
from .mcp import (
    McpServeResult,
    serve_mcp_cmd,
)
from .plugins import (
    add_plugin,
    disable_all_plugins,
    disable_plugin,
    enable_all_plugins,
    enable_plugin,
    inspect_plugin,
    list_plugins,
    remove_plugin,
)
from .runtime import (
    ConfigApplyResult,
    ConfigValidationResult,
    RuntimeRunResult,
    apply_config_cmd,
    run_harness_cmd,
    start_harness,
    validate_config_cmd,
)
from .skills import (
    export_skill_graph_visual_cmd,
    find_skill_chain_cmd,
    get_skill_topology_cmd,
    index_skills_cmd,
    route_skills_cmd,
    scaffold_skill_cmd,
    validate_skill_cmd,
)
from .system import list_services, run_introspect
from .tools import disable_tool, enable_tool, list_tools, toggle_tool
from .workspace import (
    WorkspaceInitResult,
    init_workspace_cmd,
    watch_workspace_cmd,
)

logger = structlog.get_logger()


@dataclass
class CommandDescriptor:
    """Metadata descriptor for a registered Harness command."""

    name: str
    category: str
    description: str
    handler: Callable[..., Any]
    is_async: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "is_async": self.is_async,
        }


class CommandRegistry:
    """Authoritative registry and dispatcher for all Harness operations."""

    _commands: dict[str, CommandDescriptor] = {}

    @classmethod
    def register(
        cls,
        name: str,
        handler: Callable[..., Any],
        category: str = "general",
        description: str = "",
    ) -> None:
        """Register a command into the central command engine."""
        is_async = inspect.iscoroutinefunction(handler)
        doc = description or (inspect.getdoc(handler) or "").split("\n")[0]
        cls._commands[name] = CommandDescriptor(
            name=name,
            category=category,
            description=doc,
            handler=handler,
            is_async=is_async,
        )

    @classmethod
    def get(cls, name: str) -> CommandDescriptor | None:
        """Retrieve a command descriptor by name."""
        return cls._commands.get(name)

    @classmethod
    def list_commands(cls, category: str | None = None) -> list[CommandDescriptor]:
        """List all registered commands, optionally filtered by category."""
        cmds = list(cls._commands.values())
        if category:
            cmds = [c for c in cmds if c.category == category]
        return cmds

    @classmethod
    async def dispatch(cls, name: str, **kwargs: Any) -> Any:
        """Dispatch a registered command by name with arguments and emit execution telemetry."""
        descriptor = cls.get(name)
        if not descriptor:
            raise KeyError(f"Unknown command: '{name}'")

        start = time.perf_counter()
        logger.info("Dispatching command", command=name, category=descriptor.category)

        try:
            if descriptor.is_async:
                result = await descriptor.handler(**kwargs)
            else:
                result = descriptor.handler(**kwargs)

            duration = time.perf_counter() - start
            logger.info("Command completed", command=name, duration=round(duration, 4))
            return result
        except Exception as e:
            duration = time.perf_counter() - start
            logger.error("Command failed", command=name, error=str(e), duration=round(duration, 4))
            raise


# Auto-populate the CommandRegistry with standard Harness operations
_BUILTIN_COMMANDS: list[tuple[str, Callable[..., Any], str, str]] = [
    ("workspace.init", init_workspace_cmd, "workspace", "Initialize workspace directory and config"),
    ("workspace.watch", watch_workspace_cmd, "workspace", "Start live hot-reloading watcher"),
    ("runtime.run", run_harness_cmd, "runtime", "Start the Harness runtime"),
    ("runtime.apply", apply_config_cmd, "runtime", "Apply declarative config tree"),
    ("runtime.validate_config", validate_config_cmd, "runtime", "Validate declarative config schema"),
    ("mcp.serve", serve_mcp_cmd, "mcp", "Start the MCP STDIO server"),
    ("compute.assess", assess_compute_cmd, "compute", "Assess task complexity and model tiering"),
    ("events.get", get_events_cmd, "events", "Query append-only event stream"),
    ("agent.run", run_agent, "agent", "Execute autonomous agent task"),
    ("creator.scaffold", scaffold_plugin_cmd, "creator", "Scaffold plugin project"),
    ("creator.validate", validate_plugin_cmd, "creator", "Validate plugin project"),
    ("creator.remediate", remediate_plugin_cmd, "creator", "Auto-remediate plugin project"),
    ("creator.archetypes", list_archetypes_cmd, "creator", "List plugin archetype presets"),
    ("plugin.add", add_plugin, "plugin", "Add and ingest plugin"),
    ("plugin.list", list_plugins, "plugin", "List installed plugins"),
    ("plugin.enable", enable_plugin, "plugin", "Enable plugin"),
    ("plugin.disable", disable_plugin, "plugin", "Disable plugin"),
    ("plugin.enable_all", enable_all_plugins, "plugin", "Enable all plugins"),
    ("plugin.disable_all", disable_all_plugins, "plugin", "Disable all plugins"),
    ("plugin.inspect", inspect_plugin, "plugin", "Inspect plugin manifest"),
    ("plugin.remove", remove_plugin, "plugin", "Remove plugin"),
    ("skills.index", index_skills_cmd, "skills", "Index workspace skill knowledge graph"),
    ("skills.route", route_skills_cmd, "skills", "Route intent to matching skills"),
    ("skills.chain", find_skill_chain_cmd, "skills", "Find execution chain between skills"),
    ("skills.info", get_skill_topology_cmd, "skills", "Get skill topological dependencies"),
    ("skills.scaffold", scaffold_skill_cmd, "skills", "Scaffold new agent skill package"),
    ("skills.validate", validate_skill_cmd, "skills", "Validate agent skill standards"),
    ("skills.visual", export_skill_graph_visual_cmd, "skills", "Generate skill graph visual brief"),
    ("bridge.list", list_bridges_cmd, "bridge", "List registered ecosystem bridges"),
    ("bridge.status", check_bridge_status_cmd, "bridge", "Check ecosystem bridge substrate status"),
    ("system.services", list_services, "system", "List registered service keys"),
    ("system.introspect", run_introspect, "system", "Generate system introspection diagnostics"),
    ("tools.list", list_tools, "tools", "List available tools"),
    ("tools.enable", enable_tool, "tools", "Enable tool"),
    ("tools.disable", disable_tool, "tools", "Disable tool"),
    ("tools.toggle", toggle_tool, "tools", "Toggle tool enablement"),
]

for cmd_name, cmd_handler, cmd_cat, cmd_doc in _BUILTIN_COMMANDS:
    CommandRegistry.register(cmd_name, cmd_handler, category=cmd_cat, description=cmd_doc)


__all__ = [
    "CommandDescriptor",
    "CommandRegistry",
    "ComputeAssessmentResult",
    "ConfigApplyResult",
    "ConfigValidationResult",
    "EventQueryResult",
    "FallbackLLM",
    "McpServeResult",
    "RuntimeRunResult",
    "WorkspaceInitResult",
    "add_plugin",
    "apply_config_cmd",
    "assess_compute_cmd",
    "build_plugin_cmd",
    "check_bridge_status_cmd",
    "disable_all_plugins",
    "disable_plugin",
    "disable_tool",
    "enable_all_plugins",
    "enable_plugin",
    "enable_tool",
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_events_cmd",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "init_workspace_cmd",
    "inspect_plugin",
    "list_archetypes_cmd",
    "list_bridges_cmd",
    "list_plugins",
    "list_services",
    "list_tools",
    "remediate_plugin_cmd",
    "remove_plugin",
    "route_skills_cmd",
    "run_agent",
    "run_harness_cmd",
    "run_introspect",
    "scaffold_plugin_cmd",
    "scaffold_skill_cmd",
    "serve_mcp_cmd",
    "start_harness",
    "toggle_tool",
    "validate_config_cmd",
    "validate_plugin_cmd",
    "validate_skill_cmd",
    "watch_workspace_cmd",
]
