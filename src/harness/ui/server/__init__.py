"""FastAPI UI server and WebSocket broadcaster for Brain Harness.

Supports either a unified HarnessRuntime or individual kernel instances.
"""

from __future__ import annotations

from harness.ui.server.adapter import RuntimeAdapter
from harness.ui.server.app import create_app
from harness.ui.server.models import (
    CreatorScaffoldRequest,
    CreatorValidateRequest,
    PluginIngestRequest,
    PluginToggleRequest,
    SwarmRunRequest,
    SwarmSkillDispatchRequest,
    TaskRequest,
    ToolToggleRequest,
)
from harness.ui.server.swarm_graph import build_swarm_mermaid_graph

__all__ = [
    "CreatorScaffoldRequest",
    "CreatorValidateRequest",
    "PluginIngestRequest",
    "PluginToggleRequest",
    "RuntimeAdapter",
    "SwarmRunRequest",
    "SwarmSkillDispatchRequest",
    "TaskRequest",
    "ToolToggleRequest",
    "build_swarm_mermaid_graph",
    "create_app",
]
