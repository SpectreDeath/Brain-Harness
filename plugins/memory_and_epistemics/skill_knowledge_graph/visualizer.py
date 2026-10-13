"""Interactive HTML Visual Brief and Mermaid diagram generator for Skill Knowledge Graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from harness.services.skill_graph import EdgeType
from harness.services.skill_visualizer import SkillGraphVisualizer


def render_mermaid(
    nodes: dict[str, Any],
    edges: list[Any],
) -> str:
    """Generate Mermaid diagram markdown representing the full skill knowledge graph."""
    lines = ["flowchart TD"]

    # Group by category
    cat_to_skills: dict[str, list[str]] = defaultdict(list)
    for name, node in nodes.items():
        cat_to_skills[node.category].append(name)

    for cat, s_names in sorted(cat_to_skills.items()):
        clean_cat = cat.replace("/", "_").replace("-", "_")
        lines.append(f'    subgraph sg_{clean_cat} ["{cat.upper()}"]')
        for s in sorted(s_names):
            skill = nodes[s]
            label = f"{skill.name}\\n({skill.invocation or skill.name})"
            lines.append(f'        node_{s.replace("-", "_")}["{label}"]')
        lines.append("    end")

    # Add Edges
    for edge in edges:
        if edge.source in nodes and edge.target in nodes:
            src_id = f"node_{edge.source.replace('-', '_')}"
            tgt_id = f"node_{edge.target.replace('-', '_')}"
            rel_label = edge.relation.value

            if edge.relation == EdgeType.PRECEDES:
                lines.append(f"    {src_id} -->|{rel_label}| {tgt_id}")
            elif edge.relation == EdgeType.REQUIRES:
                lines.append(f"    {src_id} -.->|{rel_label}| {tgt_id}")
            elif edge.relation == EdgeType.COMPLEMENTS:
                lines.append(f"    {src_id} <-->|{rel_label}| {tgt_id}")

    return "\n".join(lines)


__all__ = ["SkillGraphVisualizer", "render_mermaid"]
