"""Task intent analysis, prerequisite resolution, and topological execution planning."""

from __future__ import annotations

from typing import Any, Callable

import structlog

from harness.kernel.graph import DependencyGraph, GraphCycleError
from harness.services.skill_clustering.engine.scoring import (
    resolve_candidates_and_prereqs,
    score_skills_for_task,
)
from harness.services.skill_clustering.engine.tokens import tokenize
from harness.services.skill_clustering.models import (
    EmergentCapability,
    SkillSelectionPlan,
)

logger = structlog.get_logger()


def select_skills_for_task(
    skills: dict[str, Any],
    registry: Any,
    task: str,
    max_skills: int = 5,
    include_verifier: bool = True,
    tokenize_fn: Callable[[str], set[str]] | None = None,
    emergent_discover_fn: Callable[..., list[EmergentCapability]] | None = None,
) -> SkillSelectionPlan:
    """Analyze task intent and synthesize a prerequisite-aware execution plan."""
    tok_fn = tokenize_fn or tokenize
    task_clean = task.strip().lower()
    task_tokens = tok_fn(task_clean)

    matched_cap: EmergentCapability | None = None
    if emergent_discover_fn is not None:
        emergent_caps = emergent_discover_fn(query=task)
        matched_cap = emergent_caps[0] if emergent_caps else None

    skill_scores = score_skills_for_task(
        skills, registry, task_clean, task_tokens, max_skills=max_skills, tok_fn=tok_fn
    )

    selected_skills, immediate_prereqs, primary_cluster = resolve_candidates_and_prereqs(
        skills, skill_scores, matched_cap, max_skills=max_skills
    )

    candidate_nodes: list[str] = [p for p in immediate_prereqs if p not in selected_skills] + list(selected_skills)

    # Topologically sort candidate skills using DependencyGraph
    dag: DependencyGraph[str] = DependencyGraph()
    for node in candidate_nodes:
        dag.add_node(node)

    for s_name in candidate_nodes:
        s_obj = skills.get(s_name)
        if not s_obj:
            continue
        deps = getattr(s_obj, "dependencies", []) or getattr(s_obj, "references", []) or []
        for dep in deps:
            clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
            if clean_dep in candidate_nodes and clean_dep != s_name:
                if clean_dep in dag.transitive_dependents(s_name):
                    continue
                dag.add_edge(from_node=clean_dep, to_node=s_name)

    if matched_cap and matched_cap.recommended_pipeline:
        rec = [s for s in matched_cap.recommended_pipeline if s in candidate_nodes]
        for i in range(len(rec) - 1):
            s_from, s_to = rec[i], rec[i + 1]
            if s_from != s_to and s_from not in dag.transitive_dependents(s_to):
                dag.add_edge(from_node=s_from, to_node=s_to)

    try:
        sorted_pipeline = dag.topological_sort()
        pipeline = [n for n in sorted_pipeline if n in candidate_nodes]
        for n in candidate_nodes:
            if n not in pipeline:
                pipeline.append(n)
    except GraphCycleError:
        pipeline = list(candidate_nodes)

    verifier_skill = None
    if include_verifier:
        for v in ("adversarial-agent-verifier", "questio-reflection", "code-review"):
            if v in skills:
                verifier_skill = v
                break

    if verifier_skill:
        if verifier_skill in pipeline:
            pipeline.remove(verifier_skill)
        pipeline.append(verifier_skill)

    # Assemble ordered stages with crisp completion gates
    assembled_stages: list[dict[str, Any]] = []
    active_anti_patterns: list[dict[str, str]] = []
    active_invariants: list[dict[str, Any]] = []
    seen_ap: set[str] = set()
    seen_inv: set[str] = set()

    for s_name in pipeline:
        s_obj = skills.get(s_name)
        if not s_obj:
            continue
        stages = getattr(s_obj, "stages", []) or []
        if stages:
            for st in stages:
                assembled_stages.append({
                    "skill": s_name,
                    "stage_num": getattr(st, "stage_num", 1),
                    "name": getattr(st, "name", "Stage"),
                    "completion_gate": getattr(st, "completion_gate", "") or getattr(st, "objective", ""),
                })
        else:
            assembled_stages.append({
                "skill": s_name,
                "stage_num": 1,
                "name": f"Execute {s_name}",
                "completion_gate": f"Output artifact from {s_name} generated",
            })

        for ap in getattr(s_obj, "anti_patterns", []):
            ap_name = getattr(ap, "name", "")
            if ap_name and ap_name not in seen_ap:
                seen_ap.add(ap_name)
                active_anti_patterns.append({
                    "skill": s_name,
                    "anti_pattern": ap_name,
                    "symptom": getattr(ap, "symptom", "") or getattr(ap, "description", ""),
                    "remedy": getattr(ap, "remedy", "") or getattr(ap, "mitigation", ""),
                })

        for inv in getattr(s_obj, "invariants", []):
            rule = getattr(inv, "rule", "")
            if rule and rule not in seen_inv:
                seen_inv.add(rule)
                active_invariants.append({
                    "skill": s_name,
                    "rule": rule,
                    "is_blocking": getattr(inv, "is_blocking", True),
                })

    top_score = skill_scores[0][0] if skill_scores else 1.0
    confidence = min(0.98, max(0.35, 0.4 + (top_score / 15.0)))
    if matched_cap:
        confidence = min(0.99, confidence + 0.15)

    if matched_cap:
        rationale = (
            f"Task strongly matched emergent capability '{matched_cap.title}' ({matched_cap.id}). "
            f"Assembled topological pipeline: {' → '.join(pipeline)}. "
            f"{matched_cap.novelty_rationale}"
        )
    else:
        rationale = (
            f"Task routed to top matching domain skills: {', '.join(selected_skills[:3])}. "
            f"Topological pipeline chained {len(pipeline)} skills with {len(assembled_stages)} execution gates "
            f"and {len(active_anti_patterns)} guarded anti-patterns."
        )

    return SkillSelectionPlan(
        task=task,
        selected_skills=selected_skills,
        execution_pipeline=pipeline,
        emergent_capability=matched_cap,
        primary_cluster=primary_cluster,
        prerequisites=immediate_prereqs,
        stages=assembled_stages,
        active_anti_patterns=active_anti_patterns[:8],
        active_invariants=active_invariants[:8],
        recommended_verifier=verifier_skill,
        confidence=round(confidence, 3),
        rationale=rationale,
    )
