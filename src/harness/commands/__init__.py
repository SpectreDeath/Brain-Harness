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
    "inspect_plugin",
    "list_archetypes_cmd",
    "list_plugins",
    "list_services",
    "list_tools",
    "remove_plugin",
    "run_agent",
    "run_introspect",
    "scaffold_plugin_cmd",
    "toggle_tool",
    "validate_plugin_cmd",
]
