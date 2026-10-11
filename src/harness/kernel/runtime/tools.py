"""Tool control, task execution, and session export operations for Harness Runtime."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from harness.agent.base import AgentLoopService
    from harness.kernel.runtime.coordinator import HarnessRuntime

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def enable_tool(runtime: HarnessRuntime, name: str) -> bool:
    """Enable an individual tool by name."""
    if runtime.tools is not None:
        return bool(runtime.tools.enable_tool(name))
    return False


def disable_tool(runtime: HarnessRuntime, name: str) -> bool:
    """Disable an individual tool by name."""
    if runtime.tools is not None:
        return bool(runtime.tools.disable_tool(name))
    return False


def toggle_tool(runtime: HarnessRuntime, name: str, enabled: bool | None = None) -> bool:
    """Toggle an individual tool's enabled state."""
    if runtime.tools is not None:
        return bool(runtime.tools.toggle_tool(name, enabled=enabled))
    return False


async def run_runtime_task(
    runtime: HarnessRuntime,
    task: str,
    *,
    max_steps: int = 10,
    context: dict[str, Any] | None = None,
) -> Any:
    """Run an autonomous task using the active agent loop service."""
    from harness.agent.base import AGENT_LOOP_KEY

    agent: AgentLoopService = runtime.context.require(AGENT_LOOP_KEY)
    return await agent.run_task(task, max_steps=max_steps, context=context)


async def export_runtime_session(
    runtime: HarnessRuntime,
    session_id: str,
    format: str = "json",
) -> str:
    """Export an agent execution session to JSON or Markdown."""
    mgr = runtime.sessions
    if mgr is None:
        raise RuntimeError("Agent session manager is not available in runtime")
    return str(await mgr.export_session(session_id, format=format))


__all__ = [
    "disable_tool",
    "enable_tool",
    "export_runtime_session",
    "run_runtime_task",
    "toggle_tool",
]
