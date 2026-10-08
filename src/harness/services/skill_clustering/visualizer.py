"""Mermaid visualizer for skill clusters and cross-cluster bridges."""

from __future__ import annotations

import re

from harness.services.skill_clustering.models import CrossClusterBridge, SkillCluster


def generate_clustered_mermaid(
    clusters: list[SkillCluster],
    bridges: list[CrossClusterBridge] | None = None,
) -> str:
    """Generate high-fidelity dark-mode Mermaid DAG visualizing skill clusters and cross-cluster bridges."""
    lines = [
        "graph TD",
        "  classDef hubSkill fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#eff6ff;",
        "  classDef memberSkill fill:#161b22,stroke:#30363d,stroke-width:1px,color:#c9d1d9;",
    ]

    if not clusters:
        lines.append('  emptyRoot["No active skill clusters discovered"]')
        return "\n".join(lines)

    for c in clusters:
        clean_cid = re.sub(r"[^a-zA-Z0-9_]", "_", c.cluster_id)
        escaped_title = f"{c.name} (Cohesion: {c.cohesion_score:.2f})".replace('"', "'")
        lines.append(f'  subgraph {clean_cid} ["{escaped_title}"]')
        for skill in c.skills:
            clean_sid = re.sub(r"[^a-zA-Z0-9_]", "_", skill)
            if skill == c.central_hub_skill:
                lines.append(f'    {clean_sid}["★ {skill}"]:::hubSkill')
            else:
                lines.append(f'    {clean_sid}["{skill}"]:::memberSkill')
        lines.append("  end")

    if bridges:
        for b in bridges:
            clean_src = re.sub(r"[^a-zA-Z0-9_]", "_", b.source_cluster)
            clean_dst = re.sub(r"[^a-zA-Z0-9_]", "_", b.target_cluster)
            desc = b.synergy_description[:40].replace('"', "'")
            lines.append(f'  {clean_src} -.->|"{desc}"| {clean_dst}')

    return "\n".join(lines)


__all__ = ["generate_clustered_mermaid"]
