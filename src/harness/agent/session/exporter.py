"""Session and Execution Tree rendering, transcript generation, and schema export engine.

Provides Markdown transcripts, JSON exports, and hierarchical ASCII tree representations.

Architectural Layering:
- `SessionTreeExporter` (this module) is the pure stateless renderer/serializer for sessions
  and execution trees (`to_markdown`, `to_json`, `to_ascii_tree`).
- `SessionExportMixin` in `harness.agent.session.manager.export` is the stateful manager
  mixin that resolves sessions from `AgentSessionStore` and delegates to this serializer.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from harness.agent.session.models import AgentSession, SessionTreeNode, SessionTreeSnapshot


class SessionTreeExporter:
    """Renderer and serializer for agent sessions and hierarchical execution trees."""

    @staticmethod
    def to_markdown(session: AgentSession) -> str:
        """Render session execution history as a clean markdown document."""
        lines = [
            f"# Agent Execution Session: `{session.session_id}`",
            "",
            f"- **Task**: {session.task}",
            f"- **Status**: `{session.status}`",
            f"- **Created**: {time.ctime(session.created_at)}",
            f"- **Steps Executed**: {len(session.steps)}",
            f"- **Total Tokens**: {session.total_tokens}",
        ]
        if session.parent_session_id:
            lines.append(f"- **Parent Session**: `{session.parent_session_id}`")
        if session.node_id or session.role:
            lines.append(f"- **Node / Role**: `{session.node_id or 'none'}` ({session.role or 'default'})")
        if session.children_session_ids:
            lines.append(f"- **Child Sessions**: {len(session.children_session_ids)}")
        if session.completed_at:
            duration = session.completed_at - session.created_at
            lines.append(f"- **Duration**: {duration:.2f}s")
        lines.append("")

        if session.final_answer:
            lines.extend(["## Final Answer", "", session.final_answer, ""])

        lines.extend(["## Step Trajectory", ""])
        for step in session.steps:
            lines.append(f"### Step {step.step_number}")
            if step.thought:
                lines.append(f"**Thought:** {step.thought}")
            if step.action:
                lines.append(f"**Action:** `{step.action}`")
                lines.append("```json")
                lines.append(json.dumps(step.action_input, indent=2))
                lines.append("```")
            if step.observation is not None:
                lines.append("**Observation:**")
                lines.append("```json" if isinstance(step.observation, (dict, list)) else "")
                lines.append(
                    json.dumps(step.observation, indent=2)
                    if isinstance(step.observation, (dict, list))
                    else str(step.observation)
                )
                if isinstance(step.observation, (dict, list)):
                    lines.append("```")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_json(target: Any) -> str:
        """Serialize session, tree node, or tree snapshot to formatted JSON string."""
        if hasattr(target, "to_dict"):
            data = target.to_dict()
        elif isinstance(target, dict):
            data = target
        else:
            raise TypeError(f"Cannot serialize object of type {type(target)} to session JSON")
        return json.dumps(data, indent=2)

    @classmethod
    def render_ascii_tree(cls, target: SessionTreeSnapshot | SessionTreeNode) -> str:
        """Render hierarchical execution tree as clean ASCII tree diagram."""
        from harness.agent.session.models import SessionTreeSnapshot

        root = target.root if isinstance(target, SessionTreeSnapshot) else target
        lines: list[str] = []

        def _format_node(node: SessionTreeNode) -> str:
            role_tag = f" [{node.role}]" if node.role else ""
            status_tag = f" ({node.status})"
            tokens_tag = f" - {node.total_tokens} tokens" if node.total_tokens else ""
            return f"{node.session_id}{role_tag}{status_tag}: {node.task[:50]}{tokens_tag}"

        lines.append(_format_node(root))

        def _walk_children(children: tuple[SessionTreeNode, ...], prefix: str = "") -> None:
            count = len(children)
            for i, child in enumerate(children):
                is_last = (i == count - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{_format_node(child)}")
                sub_prefix = prefix + ("    " if is_last else "│   ")
                if child.children:
                    _walk_children(child.children, sub_prefix)

        if root.children:
            _walk_children(root.children)

        return "\n".join(lines)
