"""Pairwise structural and semantic affinity computation with degree normalization."""

from __future__ import annotations

import collections
import math
from typing import Any, Callable

from harness.services.skill_clustering.engine.tokens import tokenize


def compute_affinity_matrix(
    skills: dict[str, Any],
    registry: Any = None,
    tokenize_fn: Callable[[str], set[str]] | None = None,
) -> dict[str, dict[str, float]]:
    """Compute pairwise structural and semantic affinity weights between skills with degree normalization."""
    tok_fn = tokenize_fn or tokenize
    skill_tokens: dict[str, set[str]] = {}
    in_degrees: dict[str, int] = collections.defaultdict(int)

    for name, s in skills.items():
        category = getattr(s, "category", "") or ""
        target = getattr(s, "target", "") or ""
        description = getattr(s, "description", "") or ""
        triggers = getattr(s, "triggers", []) or []
        stages = getattr(s, "stages", []) or []
        stage_names = " ".join(getattr(st, "name", "") for st in stages)

        text = f"{name} {category} {description} {target} {' '.join(triggers)} {stage_names}"
        skill_tokens[name] = tok_fn(text)

        deps = set(getattr(s, "dependencies", []) or getattr(s, "references", []) or [])
        for dep in deps:
            if dep in skills:
                in_degrees[dep] += 1

    adj: dict[str, dict[str, float]] = collections.defaultdict(dict)

    for s1, node1 in skills.items():
        deps1 = set(getattr(node1, "dependencies", []) or getattr(node1, "references", []) or [])
        cat1 = (getattr(node1, "category", "") or "").lower()
        cat1_prefix = cat1.split("/")[0].strip()

        for s2, node2 in skills.items():
            if s1 == s2:
                continue

            deps2 = set(getattr(node2, "dependencies", []) or getattr(node2, "references", []) or [])
            cat2 = (getattr(node2, "category", "") or "").lower()
            cat2_prefix = cat2.split("/")[0].strip()

            weight = 0.0

            # 1. Topological dependencies & references with degree dampening (Rule of specificity)
            if s2 in deps1:
                deg2 = in_degrees.get(s2, 1)
                dampener = 1.0 / math.log2(2.0 + deg2)
                weight += 4.5 * dampener
            if s1 in deps2:
                deg1 = in_degrees.get(s1, 1)
                dampener = 1.0 / math.log2(2.0 + deg1)
                weight += 4.5 * dampener

            # 1b. Authoritative typed edge affinity when registry is present
            if registry is not None and hasattr(registry, "_edge_keys"):
                from harness.services.skill_graph import EdgeType
                edge_keys = registry._edge_keys
                if (s1, s2, EdgeType.PRECEDES) in edge_keys or (s2, s1, EdgeType.PRECEDES) in edge_keys:
                    weight += 1.2
                if (s1, s2, EdgeType.COMPLEMENTS) in edge_keys or (s2, s1, EdgeType.COMPLEMENTS) in edge_keys:
                    weight += 1.5

            # 2. Shared dependencies (co-referencing)
            common_deps = deps1 & deps2
            if common_deps:
                weight += min(len(common_deps) * 0.8, 2.0)

            # 3. Category hierarchy alignment
            if cat1 and cat2 and cat1 != "general" and cat2 != "general":
                if cat1 == cat2:
                    weight += 2.5
                elif cat1_prefix == cat2_prefix:
                    weight += 1.5

            # 4. Semantic token Jaccard similarity
            tok1 = skill_tokens[s1]
            tok2 = skill_tokens[s2]
            if tok1 and tok2:
                jaccard = len(tok1 & tok2) / len(tok1 | tok2)
                if jaccard > 0.07:
                    weight += jaccard * 5.0

            # Threshold to keep graph sparse and meaningful
            if weight >= 1.6:
                adj[s1][s2] = weight

    return adj
