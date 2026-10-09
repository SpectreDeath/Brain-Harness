"""ReAct Agent Subpackage — autonomous Reason + Act execution loop.

Coordinates LLM reasoning with tool dispatching, transactional boundaries,
and event telemetry.
"""

from __future__ import annotations

from .dispatch import (
    dispatch_native_tool_calls,
    dispatch_text_fallback_action,
)
from .engine import StepExecutionEngine
from .loop import ReActAgentLoop
from .plugin import ReActAgentPlugin, plugin
from .prompting import (
    build_react_initial_messages,
    extract_action_from_thought,
)
from .resolvers import resolve_react_agent_loop
from .transactions import invoke_tool_transactional

__all__ = [
    "ReActAgentLoop",
    "ReActAgentPlugin",
    "StepExecutionEngine",
    "build_react_initial_messages",
    "dispatch_native_tool_calls",
    "dispatch_text_fallback_action",
    "extract_action_from_thought",
    "invoke_tool_transactional",
    "plugin",
    "resolve_react_agent_loop",
]
