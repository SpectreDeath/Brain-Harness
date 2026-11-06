"""Pipeline ordering and guarded invariant/anti-pattern extraction helpers."""

from __future__ import annotations

from collections import deque
from typing import Any


def extract_guarded_items(
    skills: dict[str, Any], skill_names: list[str]
) -> tuple[list[str], list[str]]:
    """Extract unique guarded anti-patterns and guaranteed invariants for a list of skills."""
    guarded_aps: list[str] = []
    guaranteed_invs: list[str] = []
    for s_name in skill_names:
        s_obj = skills.get(s_name)
        if not s_obj:
            continue
        for ap in getattr(s_obj, "anti_patterns", []) or []:
            ap_name = getattr(ap, "name", "")
            if ap_name and ap_name not in guarded_aps:
                guarded_aps.append(ap_name)
        for inv in getattr(s_obj, "invariants", []) or []:
            inv_rule = getattr(inv, "rule", "")
            if inv_rule and inv_rule not in guaranteed_invs:
                guaranteed_invs.append(inv_rule)
    return guarded_aps[:6], guaranteed_invs[:6]


def order_cluster_pipeline(
    cand_members: list[str],
    skills: dict[str, Any],
    hub_skill: str,
) -> list[str]:
    """Topologically order cluster member candidates along internal dependency edges."""
    cand_set = set(cand_members)
    in_degree = {m: 0 for m in cand_members}
    out_degree = {m: 0 for m in cand_members}
    adj: dict[str, list[str]] = {m: [] for m in cand_members}

    for m in cand_members:
        node = skills.get(m)
        deps = (
            getattr(node, "dependencies", [])
            or getattr(node, "references", [])
            or []
        )
        for d in deps:
            if d in cand_set and d != m:
                adj[d].append(m)
                in_degree[m] += 1
                out_degree[d] += 1

    connected_roots = [
        m for m in cand_members if in_degree[m] == 0 and out_degree[m] > 0
    ]
    connected_roots.sort(
        key=lambda m: (
            out_degree[m],
            len(getattr(skills.get(m), "dependencies", []) or []),
            m == hub_skill,
        ),
        reverse=True,
    )

    queue = deque(connected_roots)
    ordered: list[str] = []
    curr_in_degree = dict(in_degree)

    while queue:
        curr = queue.popleft()
        if curr not in ordered:
            ordered.append(curr)
        sorted_neighbors = sorted(
            adj[curr],
            key=lambda n: (out_degree[n], n == hub_skill),
            reverse=True,
        )
        for neighbor in sorted_neighbors:
            curr_in_degree[neighbor] -= 1
            if curr_in_degree[neighbor] == 0 and neighbor not in ordered:
                queue.append(neighbor)

    remaining_connected = [
        m
        for m in cand_members
        if m not in ordered and (out_degree[m] > 0 or in_degree[m] > 0)
    ]
    if remaining_connected:
        remaining_connected.sort(
            key=lambda m: (out_degree[m] + in_degree[m], m == hub_skill),
            reverse=True,
        )
        for m in remaining_connected:
            if m not in ordered:
                ordered.append(m)

    isolated = [m for m in cand_members if m not in ordered]
    isolated.sort(
        key=lambda m: (
            m == hub_skill,
            len(getattr(skills.get(m), "dependencies", []) or []),
        ),
        reverse=True,
    )
    ordered.extend(isolated)
    return ordered[: min(5, len(ordered))]
