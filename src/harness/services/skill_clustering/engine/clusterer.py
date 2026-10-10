"""Functional community detection and SkillCluster construction."""

from __future__ import annotations

import collections
from typing import Any, Callable

from harness.services.skill_clustering.engine.emergent import synthesize_cluster_capabilities
from harness.services.skill_clustering.models import SkillCluster


def cluster_skills(
    skills: dict[str, Any],
    affinity_matrix: dict[str, dict[str, float]],
    min_cluster_size: int = 2,
    tokenize_fn: Callable[[str], set[str]] | None = None,
) -> list[SkillCluster]:
    """Cluster skills into functional domains using modular community detection."""
    skills_list = sorted(skills.keys())

    # Seed initial labels
    labels: dict[str, str] = {s: s for s in skills_list}

    # Multi-pass Label Propagation with deterministic tie-breaking
    for _ in range(10):
        changed = False
        for s in skills_list:
            neighbor_weights: dict[str, float] = collections.defaultdict(float)
            # Self-reinforcement
            neighbor_weights[labels[s]] += 1.0

            for nbr, w in affinity_matrix.get(s, {}).items():
                neighbor_weights[labels[nbr]] += w

            best_label = max(
                neighbor_weights.items(), key=lambda item: (item[1], -len(item[0]), item[0])
            )[0]

            if best_label != labels[s]:
                labels[s] = best_label
                changed = True

        if not changed:
            break

    # Group into raw clusters
    raw_clusters: dict[str, list[str]] = collections.defaultdict(list)
    for s, label in labels.items():
        raw_clusters[label].append(s)

    # Split mega-clusters (size > 14) along secondary category sub-partitions
    refined_clusters: list[list[str]] = []
    for members in raw_clusters.values():
        if len(members) <= 14:
            refined_clusters.append(sorted(members))
        else:
            sub_groups: dict[str, list[str]] = collections.defaultdict(list)
            for m in members:
                m_cat = getattr(skills[m], "category", "general")
                clean_cat = m_cat.split("/")[0].strip()
                sub_groups[clean_cat].append(m)

            for sub_members in sub_groups.values():
                refined_clusters.append(sorted(sub_members))

    # Re-merge singletons into best matching clusters
    final_clusters_lists: list[list[str]] = []
    singletons: list[str] = []
    for c in refined_clusters:
        if len(c) >= min_cluster_size:
            final_clusters_lists.append(c)
        else:
            singletons.extend(c)

    for s in singletons:
        best_c: list[str] | None = None
        max_aff = -1.0
        for c in final_clusters_lists:
            aff = sum(affinity_matrix.get(s, {}).get(m, 0.0) for m in c)
            if aff > max_aff:
                max_aff = aff
                best_c = c
        if best_c:
            best_c.append(s)
        elif final_clusters_lists:
            final_clusters_lists[0].append(s)
        else:
            final_clusters_lists.append([s])

    # Filter strictly by min_cluster_size
    final_clusters_lists = [c for c in final_clusters_lists if len(c) >= min_cluster_size]

    # Construct formal SkillCluster objects
    clusters: list[SkillCluster] = []
    for idx, members in enumerate(
        sorted(final_clusters_lists, key=lambda x: len(x), reverse=True), start=1
    ):
        if not members:
            continue

        # Identify central hub skill (highest internal degree)
        hub_skill = max(
            members,
            key=lambda m: sum(1 for other in members if other in (getattr(skills[m], "dependencies", []) or []))
            + sum(1 for other in members if m in (getattr(skills[other], "dependencies", []) or [])),
        )

        # Count internal edges
        internal_edges = 0
        for m in members:
            node = skills[m]
            deps = set(getattr(node, "dependencies", []) or getattr(node, "references", []) or [])
            internal_edges += len(deps.intersection(members))

        categories = sorted({getattr(skills[m], "category", "general") for m in members})
        primary_domain = categories[0] if categories else "general"

        cluster_id = f"cluster_{idx:02d}_{hub_skill.replace('-', '_')}"
        clean_name = f"{hub_skill.replace('-', ' ').title()} & Domain Peers"

        emergent_caps = synthesize_cluster_capabilities(
            skills=skills,
            members=members,
            cluster_id=cluster_id,
            hub_skill=hub_skill,
            primary_domain=primary_domain,
            tokenize_fn=tokenize_fn,
        )

        # Calculate cohesion score
        n = len(members)
        max_edges = n * (n - 1) if n > 1 else 1
        cohesion = round(min(1.0, max(0.1, internal_edges / max(1, max_edges))), 3)

        cluster = SkillCluster(
            cluster_id=cluster_id,
            name=clean_name,
            domain=primary_domain,
            skills=sorted(members),
            central_hub_skill=hub_skill,
            categories=categories,
            internal_edge_count=internal_edges,
            cohesion_score=cohesion,
            emergent_capabilities=emergent_caps,
        )
        clusters.append(cluster)

    return clusters
