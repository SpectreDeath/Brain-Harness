"""Skill intent scoring and candidate prerequisite resolution."""

from __future__ import annotations

from typing import Any, Callable

from harness.services.skill_clustering.engine.tokens import tokenize
from harness.services.skill_clustering.models import EmergentCapability


def score_skills_for_task(
    skills: dict[str, Any],
    registry: Any,
    task_clean: str,
    task_tokens: set[str],
    max_skills: int = 5,
    tok_fn: Callable[[str], set[str]] = tokenize,
) -> list[tuple[float, str]]:
    """Score individual skills against task intent, delegating to registry route_intent when available."""
    skill_scores: list[tuple[float, str]] = []
    if registry is not None and hasattr(registry, "route_intent"):
        try:
            routed = registry.route_intent(task_clean, top_k=max_skills * 2, min_confidence=0.15)
            for m in routed.get("matches", []):
                s_name = m.get("skill_name")
                conf = float(m.get("confidence", 0.0))
                if s_name and s_name in skills:
                    skill_scores.append((conf * 10.0, s_name))
        except Exception:
            pass

    scored_skills_set = {s for _, s in skill_scores}
    for name, skill in skills.items():
        if name in scored_skills_set:
            continue
        score = 0.0
        name_clean = name.replace("-", " ")
        if name_clean in task_clean:
            score += 4.0
        if name in task_clean:
            score += 3.5

        triggers = getattr(skill, "triggers", []) or []
        for t in triggers:
            t_lower = t.lower()
            if t_lower in task_clean:
                score += 3.0
            else:
                t_toks = tok_fn(t_lower)
                overlap = len(task_tokens & t_toks)
                if overlap:
                    score += 0.8 * overlap

        target = (getattr(skill, "target", "") or getattr(skill, "description", "")).lower()
        target_toks = tok_fn(target)
        overlap = len(task_tokens & target_toks)
        if overlap:
            score += 0.3 * overlap

        if score > 0.0:
            skill_scores.append((score, name))

    skill_scores.sort(key=lambda x: x[0], reverse=True)
    return skill_scores


def resolve_candidates_and_prereqs(
    skills: dict[str, Any],
    skill_scores: list[tuple[float, str]],
    matched_cap: EmergentCapability | None,
    max_skills: int = 5,
) -> tuple[list[str], list[str], str | None]:
    """Determine selected skills, immediate prerequisites, and primary cluster domain."""
    selected_skills: list[str] = []
    primary_cluster: str | None = None

    if matched_cap and matched_cap.recommended_pipeline:
        for s in matched_cap.recommended_pipeline:
            if s not in selected_skills and len(selected_skills) < max_skills:
                selected_skills.append(s)
        primary_cluster = matched_cap.cluster_id

    for _, s_name in skill_scores:
        if s_name not in selected_skills and len(selected_skills) < max_skills:
            selected_skills.append(s_name)

    if not selected_skills:
        selected_skills = ["deepen-architecture", "adversarial-agent-verifier"]

    immediate_prereqs: list[str] = []
    for s_name in selected_skills:
        s_obj = skills.get(s_name)
        if not s_obj:
            continue
        deps = getattr(s_obj, "dependencies", []) or getattr(s_obj, "references", []) or []
        for dep in deps:
            clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
            if clean_dep in skills and clean_dep not in selected_skills and clean_dep not in immediate_prereqs:
                immediate_prereqs.append(clean_dep)
                if len(immediate_prereqs) >= 2:
                    break
        if len(immediate_prereqs) >= 2:
            break

    return selected_skills, immediate_prereqs, primary_cluster
