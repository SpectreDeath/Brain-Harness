"""Harness commands — pure async entry points for every CLI action.

Each function here is a plain ``async def`` and can be called by:
- The Click CLI adapters in ``harness.cli``
- The web UI server (``harness.ui``)
- Tests (no CliRunner required)
"""

from .agent import FallbackLLM, run_agent
from .creator import (
    list_archetypes_cmd,
    scaffold_plugin_cmd,
    validate_plugin_cmd,
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

__all__ = [
    "FallbackLLM",
    "add_plugin",
    "disable_all_plugins",
    "disable_plugin",
    "disable_tool",
    "enable_all_plugins",
    "enable_plugin",
    "enable_tool",
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "inspect_plugin",
    "list_archetypes_cmd",
    "list_plugins",
    "list_services",
    "list_tools",
    "remove_plugin",
    "route_skills_cmd",
    "run_agent",
    "run_introspect",
    "scaffold_plugin_cmd",
    "scaffold_skill_cmd",
    "toggle_tool",
    "validate_plugin_cmd",
    "validate_skill_cmd",
]

