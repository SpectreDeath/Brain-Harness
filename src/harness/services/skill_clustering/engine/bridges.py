"""Cross-cluster bridge detection across distinct capability domains."""

from __future__ import annotations

import collections
from typing import Any

from harness.services.skill_clustering.models import CrossClusterBridge, SkillCluster


def detect_cross_cluster_bridges(
    skills: dict[str, Any],
    clusters: list[SkillCluster],
) -> list[CrossClusterBridge]:
    """Detect cross-cluster bridges where directed edges connect distinct capability clusters."""
    skill_to_cluster: dict[str, str] = {}
    for c in clusters:
        for s in c.skills:
            skill_to_cluster[s] = c.cluster_id

    cluster_edges: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)

    for s_name, skill in skills.items():
        src_c = skill_to_cluster.get(s_name)
        if not src_c:
            continue
        deps = getattr(skill, "dependencies", []) or getattr(skill, "references", []) or []
        for dep in deps:
            tgt_c = skill_to_cluster.get(dep)
            if tgt_c and tgt_c != src_c:
                cluster_edges[(src_c, tgt_c)].append((s_name, dep))

    bridges: list[CrossClusterBridge] = []
    for (src_c, tgt_c), pairs in cluster_edges.items():
        if len(pairs) >= 1:
            src_cluster = next((c for c in clusters if c.cluster_id == src_c), None)
            tgt_cluster = next((c for c in clusters if c.cluster_id == tgt_c), None)
            if src_cluster and tgt_cluster:
                bridges.append(
                    CrossClusterBridge(
                        source_cluster=src_c,
                        target_cluster=tgt_c,
                        bridge_skills=pairs[:5],
                        synergy_description=f"Inter-domain synthesis bridging {src_cluster.name} and {tgt_cluster.name}.",
                    )
                )

    return bridges
