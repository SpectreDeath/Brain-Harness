"""Topological dependency inspection, prerequisite closures, and BFS chaining (Rule 55)."""

from __future__ import annotations

import collections
from typing import Any

from harness.kernel.context import ServiceKey
from harness.kernel.graph import DependencyGraph, GraphCycleError
from harness.services.skill_graph.models import (
    EdgeType,
    SkillCardDefinition,
    SkillChainResult,
    SkillEdge,
    SkillTopologyReport,
)


def compute_topology_report(
    skill_name: str,
    skills_cache: dict[str, SkillCardDefinition],
    adj_out: dict[str, list[SkillEdge]],
    adj_in: dict[str, list[SkillEdge]],
) -> SkillTopologyReport:
    """Inspect topological dependencies, upstream prerequisites, downstream handoffs, and anti-patterns."""
    clean_name = skill_name.strip().lower().replace("_", "-")
    skill = skills_cache.get(clean_name)
    if not skill:
        raise KeyError(f"Skill '{skill_name}' not found in registry.")

    prereqs: list[str] = []
    downstream: list[str] = []
    complements: list[str] = []
    mitigates: list[str] = []

    for edge in adj_in.get(clean_name, []):
        if edge.source in skills_cache:
            if edge.relation == EdgeType.PRECEDES:
                prereqs.append(edge.source)
            elif edge.relation == EdgeType.REQUIRES:
                downstream.append(edge.source)
            elif edge.relation == EdgeType.COMPLEMENTS:
                complements.append(edge.source)

    for edge in adj_out.get(clean_name, []):
        if edge.relation == EdgeType.REQUIRES and edge.target in skills_cache:
            prereqs.append(edge.target)
        elif edge.relation == EdgeType.PRECEDES and edge.target in skills_cache:
            downstream.append(edge.target)
        elif edge.relation == EdgeType.COMPLEMENTS and edge.target in skills_cache:
            complements.append(edge.target)
        elif edge.relation == EdgeType.MITIGATES:
            mitigates.append(edge.target.replace("antipattern:", ""))

    for ap in skill.anti_patterns:
        if ap.name not in mitigates:
            mitigates.append(ap.name)

    return SkillTopologyReport(
        skill=skill,
        prerequisites=list(dict.fromkeys(prereqs)),
        downstream_handoffs=list(dict.fromkeys(downstream)),
        complements=list(dict.fromkeys(complements)),
        mitigated_anti_patterns=list(dict.fromkeys(mitigates)),
    )


def compute_prerequisite_closure(
    skill_name: str,
    skills_cache: dict[str, SkillCardDefinition],
    adj_out: dict[str, list[SkillEdge]],
    adj_in: dict[str, list[SkillEdge]],
) -> list[str]:
    """Compute the full transitive prerequisite closure for a skill in topological execution order."""
    clean_name = skill_name.strip().lower().replace("_", "-")
    if clean_name not in skills_cache:
        return []

    queue: collections.deque[str] = collections.deque([clean_name])
    ancestors: set[str] = set()

    while queue:
        curr = queue.popleft()
        for edge in adj_in.get(curr, []):
            if (
                edge.relation == EdgeType.PRECEDES
                and edge.source in skills_cache
                and edge.source not in ancestors
                and edge.source != clean_name
            ):
                ancestors.add(edge.source)
                queue.append(edge.source)
        for edge in adj_out.get(curr, []):
            if (
                edge.relation == EdgeType.REQUIRES
                and edge.target in skills_cache
                and edge.target not in ancestors
                and edge.target != clean_name
            ):
                ancestors.add(edge.target)
                queue.append(edge.target)

    if not ancestors:
        return []

    dag: DependencyGraph[str] = DependencyGraph()
    for anc in ancestors:
        dag.add_node(anc)

    for anc in ancestors:
        s_obj = skills_cache[anc]
        for dep in s_obj.dependencies:
            c_dep = dep.strip().lower().replace("_", "-").lstrip("/")
            if (
                c_dep in ancestors
                and c_dep != anc
                and c_dep not in dag.transitive_dependents(anc)
            ):
                dag.add_edge(from_node=c_dep, to_node=anc)

        for edge in adj_out.get(anc, []):
            if (
                edge.relation == EdgeType.PRECEDES
                and edge.target in ancestors
                and edge.target != anc
                and edge.target not in dag.transitive_dependents(anc)
            ):
                dag.add_edge(from_node=anc, to_node=edge.target)

    try:
        sorted_order = dag.topological_sort()
        return [n for n in sorted_order if n in ancestors]
    except GraphCycleError:
        return sorted(ancestors)


def evaluate_chain_feasibility(
    chain: list[str],
    skills_cache: dict[str, SkillCardDefinition],
    prereq_closure_fn: Any,
    context: Any = None,
    *,
    verify_prerequisites: bool = False,
) -> tuple[bool, list[str]]:
    """Check whether all declared service preconditions and prerequisite dependencies are satisfied."""
    missing_items: list[str] = []

    if verify_prerequisites and chain:
        chain_set = {s.strip().lower().replace("_", "-") for s in chain}
        for skill_name in chain:
            clean_name = skill_name.strip().lower().replace("_", "-")
            prereqs = prereq_closure_fn(clean_name)
            for p in prereqs:
                if p not in chain_set and p in skills_cache:
                    missing_items.append(f"prerequisite_missing:{clean_name}->{p}")

    if context is None:
        return len(missing_items) == 0, missing_items

    for skill_name in chain:
        clean_name = skill_name.strip().lower().replace("_", "-")
        skill = skills_cache.get(clean_name)
        if not skill:
            continue
        if skill.services:
            for svc_name in skill.services:
                key: ServiceKey[Any] = ServiceKey(svc_name)
                if hasattr(context, "has") and not context.has(key):
                    missing_items.append(f"{skill.name}:{svc_name}")

        if skill.tools and hasattr(context, "optional"):
            from harness.services.tools import TOOL_REGISTRY_KEY

            tool_reg = context.optional(TOOL_REGISTRY_KEY)
            if tool_reg is not None and hasattr(tool_reg, "get"):
                for tool_name in skill.tools:
                    if not tool_reg.get(tool_name):
                        missing_items.append(f"tool_missing:{skill.name}:{tool_name}")

    return len(missing_items) == 0, missing_items


def compute_skill_chain(
    start_skill: str,
    target_skill: str,
    skills_cache: dict[str, SkillCardDefinition],
    neighbors_fn: Any,
    *,
    fallback_direct: bool = False,
    include_synthetic: bool = False,
) -> SkillChainResult:
    """Calculate the shortest directed execution path between two skills using BFS (Rule 55)."""
    s_start = start_skill.strip().lower().replace("_", "-")
    s_target = target_skill.strip().lower().replace("_", "-")

    if s_start == s_target:
        return SkillChainResult(
            status="ok",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[s_start],
            length=1,
        )

    if s_start not in skills_cache or s_target not in skills_cache:
        if fallback_direct:
            return SkillChainResult(
                status="ok",
                start_skill=start_skill,
                target_skill=target_skill,
                chain=[s_start, s_target],
                length=2,
            )
        return SkillChainResult(
            status="no_path",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[],
            length=0,
        )

    queue: collections.deque[list[str]] = collections.deque([[s_start]])
    visited: set[str] = {s_start}

    while queue:
        path = queue.popleft()
        curr = path[-1]

        neighbors = neighbors_fn(
            curr, include_synthetic=(include_synthetic or fallback_direct)
        )
        for neighbor in sorted(neighbors):
            if neighbor == s_target:
                full_chain = path + [neighbor]
                return SkillChainResult(
                    status="ok",
                    start_skill=start_skill,
                    target_skill=target_skill,
                    chain=full_chain,
                    length=len(full_chain),
                )
            if neighbor not in visited and neighbor in skills_cache:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    if fallback_direct:
        return SkillChainResult(
            status="ok",
            start_skill=start_skill,
            target_skill=target_skill,
            chain=[s_start, s_target],
            length=2,
        )

    return SkillChainResult(
        status="no_path",
        start_skill=start_skill,
        target_skill=target_skill,
        chain=[],
        length=0,
    )


__all__ = [
    "compute_prerequisite_closure",
    "compute_skill_chain",
    "compute_topology_report",
    "evaluate_chain_feasibility",
]
