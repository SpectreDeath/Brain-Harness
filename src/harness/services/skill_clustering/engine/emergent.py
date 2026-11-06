"""Emergent capability synthesis and discovery across skill clusters."""

from __future__ import annotations

from typing import Any, Callable

from harness.services.skill_clustering.engine.tokens import tokenize
from harness.services.skill_clustering.models import EmergentCapability, SkillCluster
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS


def synthesize_cluster_capabilities(
    skills: dict[str, Any],
    members: list[str],
    cluster_id: str,
    hub_skill: str,
    primary_domain: str,
    tokenize_fn: Callable[[str], set[str]] | None = None,
) -> list[EmergentCapability]:
    """Match or synthesize emergent capabilities for a single skill cluster."""
    tok_fn = tokenize_fn or tokenize
    emergent_caps: list[EmergentCapability] = []

    for pat in CANONICAL_EMERGENT_PATTERNS:
        matching_core = [s for s in pat["core_skills"] if s in members]
        if len(matching_core) >= 2 or (len(pat["core_skills"]) <= 2 and len(matching_core) >= 1):
            guarded_aps: list[str] = []
            guaranteed_invs: list[str] = []
            for s_name in matching_core:
                s_obj = skills[s_name]
                for ap in getattr(s_obj, "anti_patterns", []):
                    ap_name = getattr(ap, "name", "")
                    if ap_name and ap_name not in guarded_aps:
                        guarded_aps.append(ap_name)
                for inv in getattr(s_obj, "invariants", []):
                    inv_rule = getattr(inv, "rule", "")
                    if inv_rule and inv_rule not in guaranteed_invs:
                        guaranteed_invs.append(inv_rule)

            emergent_caps.append(
                EmergentCapability(
                    id=pat["id"],
                    title=pat["title"],
                    description=pat["rationale"],
                    cluster_id=cluster_id,
                    primary_skills=matching_core,
                    recommended_pipeline=[s for s in pat["pipeline"] if s in skills],
                    novelty_rationale=pat["rationale"],
                    guarded_anti_patterns=guarded_aps[:6],
                    guaranteed_invariants=guaranteed_invs[:6],
                    keywords=sorted(pat.get("keywords", [])),
                    target_outcomes=pat["outcomes"],
                )
            )

    # Dynamic emergent capability synthesis for clusters without a canonical match
    if not emergent_caps and len(members) >= 2:
        member_targets = [
            getattr(skills[m], "target", "") or getattr(skills[m], "description", "")
            for m in members[:4]
        ]
        synth_guarded_aps: list[str] = []
        synth_invs: list[str] = []
        for m in members:
            for ap in getattr(skills[m], "anti_patterns", []):
                ap_name = getattr(ap, "name", "")
                if ap_name and ap_name not in synth_guarded_aps:
                    synth_guarded_aps.append(ap_name)
            for inv in getattr(skills[m], "invariants", []):
                inv_rule = getattr(inv, "rule", "")
                if inv_rule and inv_rule not in synth_invs:
                    synth_invs.append(inv_rule)

        synth_title = f"Composite {hub_skill.replace('-', ' ').title()} & Domain Synthesis"
        target_snippets = []
        for t in member_targets:
            if not t:
                continue
            first_sent = t.split(". ")[0].strip().rstrip(".")
            if first_sent:
                target_snippets.append(first_sent)
        targets_text = " | ".join(target_snippets[:3]) if target_snippets else "collaborative capability execution"
        synth_desc = (
            f"Integrates {', '.join(members[:4])} into an end-to-end {primary_domain} pipeline, "
            f"combining: {targets_text}."
        )

        # Autonomous vs Human-only invocation gating
        executable_members = []
        for m in members:
            s_obj = skills.get(m)
            fm = getattr(s_obj, "frontmatter", None)
            disable_model = False
            if isinstance(fm, dict):
                disable_model = fm.get("disable-model-invocation") is True
            elif hasattr(s_obj, "disable_model_invocation"):
                disable_model = getattr(s_obj, "disable_model_invocation", False) is True
            if not disable_model:
                executable_members.append(m)

        cand_members = executable_members if executable_members else members

        # Order candidate pipeline topologically along internal dependencies
        cand_set = set(cand_members)
        in_degree = {m: 0 for m in cand_members}
        adj = {m: [] for m in cand_members}
        for m in cand_members:
            node = skills.get(m)
            deps = getattr(node, "dependencies", []) or getattr(node, "references", []) or []
            for d in deps:
                if d in cand_set and d != m:
                    adj[d].append(m)
                    in_degree[m] += 1

        from collections import deque
        queue = deque(sorted([m for m in cand_members if in_degree[m] == 0]))
        ordered_pipeline: list[str] = []
        while queue:
            curr = queue.popleft()
            ordered_pipeline.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        for m in cand_members:
            if m not in ordered_pipeline:
                ordered_pipeline.append(m)

        final_pipeline = ordered_pipeline[:5]

        emergent_caps.append(
            EmergentCapability(
                id=f"cap_synth_{cluster_id}",
                title=synth_title,
                description=synth_desc,
                cluster_id=cluster_id,
                primary_skills=members[:5],
                recommended_pipeline=final_pipeline,
                novelty_rationale=(
                    f"Collectively coordinates {len(members)} peer skills to eliminate siloed execution "
                    f"in {primary_domain} with shared verification."
                ),
                guarded_anti_patterns=synth_guarded_aps[:6],
                guaranteed_invariants=synth_invs[:6],
                keywords=sorted(set(tok_fn(" ".join(members) + " " + primary_domain))),
                target_outcomes=[f"End-to-end {primary_domain} domain artifacts"],
            )
        )

    return emergent_caps


def discover_emergent_capabilities(
    skills: dict[str, Any],
    clusters: list[SkillCluster],
    query: str | None = None,
    tokenize_fn: Callable[[str], set[str]] | None = None,
) -> list[EmergentCapability]:
    """Retrieve all emergent capabilities across clusters, optionally filtered by query."""
    tok_fn = tokenize_fn or tokenize
    all_caps: list[EmergentCapability] = []
    for c in clusters:
        all_caps.extend(c.emergent_capabilities)

    unique_caps: dict[str, EmergentCapability] = {}
    for cap in all_caps:
        if cap.id not in unique_caps:
            unique_caps[cap.id] = cap

    # Ensure all canonical emergent patterns whose core skills exist in graph are included
    for pat in CANONICAL_EMERGENT_PATTERNS:
        matching_core = [s for s in pat["core_skills"] if s in skills]
        if len(matching_core) >= 2 and pat["id"] not in unique_caps:
            guarded_aps: list[str] = []
            guaranteed_invs: list[str] = []
            for s_name in matching_core:
                s_obj = skills[s_name]
                for ap in getattr(s_obj, "anti_patterns", []):
                    ap_name = getattr(ap, "name", "")
                    if ap_name and ap_name not in guarded_aps:
                        guarded_aps.append(ap_name)
                for inv in getattr(s_obj, "invariants", []):
                    inv_rule = getattr(inv, "rule", "")
                    if inv_rule and inv_rule not in guaranteed_invs:
                        guaranteed_invs.append(inv_rule)

            unique_caps[pat["id"]] = EmergentCapability(
                id=pat["id"],
                title=pat["title"],
                description=pat["rationale"],
                cluster_id="cluster_cross_domain",
                primary_skills=matching_core,
                recommended_pipeline=[s for s in pat["pipeline"] if s in skills],
                novelty_rationale=pat["rationale"],
                guarded_anti_patterns=guarded_aps[:6],
                guaranteed_invariants=guaranteed_invs[:6],
                keywords=sorted(pat.get("keywords", [])),
                target_outcomes=pat["outcomes"],
            )

    res = list(unique_caps.values())
    if not query:
        return res

    q_tokens = tok_fn(query)
    scored_caps: list[tuple[float, EmergentCapability]] = []
    for cap in res:
        cap_tokens = tok_fn(
            f"{cap.title} {cap.description} {' '.join(cap.primary_skills)} {' '.join(cap.keywords)}"
        )
        overlap = len(q_tokens & cap_tokens)
        keyword_overlap = len(q_tokens & set(cap.keywords))
        score = overlap + 2.0 * keyword_overlap
        if score > 0:
            scored_caps.append((score, cap))

    scored_caps.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored_caps]
