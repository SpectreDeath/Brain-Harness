"""Execution tree rendering in Mermaid, ASCII, and JSON schema (Rule 17)."""

from __future__ import annotations

from typing import Any

from harness.agent.swarm.models import SwarmExecutionTree


class SwarmTreeRenderer:
    """Renders hierarchical swarm execution DAG trees in multiple formats."""

    @classmethod
    def render_mermaid(cls, tree: SwarmExecutionTree) -> str:
        """Render Mermaid DAG topology annotated with execution status and metrics."""
        lines = ["graph TD"]
        for nid, node in sorted(tree.nodes.items()):
            dur_str = f"{round(node.duration, 2)}s"
            tok_str = f"{node.tokens_used}t"
            label = f"{node.id} [{node.role}]<br/>{node.status} | {dur_str} | {tok_str}"
            lines.append(f'    {nid}["{label}"]')
            for dep in sorted(node.dependencies):
                lines.append(f"    {dep} --> {nid}")
        return "\n".join(lines)

    @classmethod
    def render_ascii(cls, tree: SwarmExecutionTree) -> str:
        """Render readable ASCII tree of execution waves and critical paths."""
        lines = [
            f"Swarm Run: {tree.run_id} [{tree.status.upper()}] (duration: {tree.duration:.2f}s, tokens: {tree.total_tokens})",
            f"Objective: {tree.objective}",
        ]
        if tree.critical_path:
            lines.append(f"Critical Path: {' -> '.join(tree.critical_path)} ({tree.critical_path_duration:.2f}s)")

        lines.append("\nExecution Waves:")
        for w in tree.waves:
            node_desc = ", ".join(w.node_ids)
            lines.append(f"  Wave {w.wave_index}: [{node_desc}] ({w.duration:.2f}s, {w.total_tokens}t)")

        lines.append("\nNodes:")
        for nid, n in sorted(tree.nodes.items()):
            dep_str = f" <- [{', '.join(n.dependencies)}]" if n.dependencies else ""
            lines.append(f"  * {n.id} [{n.role}] ({n.status}): {n.duration:.2f}s, {n.tokens_used}t{dep_str}")

        return "\n".join(lines)


__all__ = ["SwarmTreeRenderer"]
