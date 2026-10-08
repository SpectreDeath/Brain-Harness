"""Execution guidance compilation and HTML visual brief export."""

from __future__ import annotations

from typing import Any

from harness.services.skill_graph.models import (
    SkillCardDefinition,
    SkillExecutionGuidance,
)


def compile_execution_guidance_plan(
    task: str,
    skills_cache: dict[str, SkillCardDefinition],
    select_skills_fn: Any,
    route_intent_fn: Any,
    get_skill_fn: Any,
    max_skills: int = 4,
    include_verifier: bool = True,
) -> SkillExecutionGuidance:
    """Compile an end-to-end execution guidance plan for an agent task with multi-tier fallback."""
    plan = select_skills_fn(
        task, max_skills=max_skills, include_verifier=include_verifier
    )
    selected_skills = list(getattr(plan, "selected_skills", []) or [])
    execution_pipeline = list(getattr(plan, "execution_pipeline", []) or [])
    stages = list(getattr(plan, "stages", []) or [])
    anti_patterns = list(getattr(plan, "active_anti_patterns", []) or [])
    confidence = float(getattr(plan, "confidence", 0.0) or 0.0)

    # Tier 3 Fallback: If clustering yielded low confidence (<0.20) or empty pipeline,
    # fallback to semantic intent routing + topological BFS chaining
    if confidence < 0.20 or not execution_pipeline:
        routed = route_intent_fn(task, top_k=max_skills)
        matches = routed.get("matches", [])
        recommended_chain = routed.get("recommended_chain", [])
        if matches:
            top_skill = matches[0]["skill_name"]
            if top_skill not in selected_skills:
                selected_skills = [top_skill]
            confidence = max(confidence, float(matches[0].get("confidence", 0.35)))
            if recommended_chain:
                execution_pipeline = list(recommended_chain)
            else:
                execution_pipeline = [top_skill]
            if include_verifier:
                verifier = "adversarial-agent-verifier"
                if (
                    verifier in skills_cache
                    and verifier not in execution_pipeline
                ):
                    execution_pipeline.append(verifier)
                    if verifier not in selected_skills:
                        selected_skills.append(verifier)
            stages = []
            anti_patterns = []
            for s_name in execution_pipeline:
                s_obj = get_skill_fn(s_name)
                if s_obj:
                    for st in s_obj.stages:
                        stages.append(
                            {
                                "skill": s_obj.name,
                                "stage_num": st.stage_num,
                                "name": st.name,
                                "completion_gate": st.completion_gate,
                            }
                        )
                    for ap in s_obj.anti_patterns:
                        anti_patterns.append(
                            {
                                "skill": s_obj.name,
                                "anti_pattern": ap.name,
                                "symptom": ap.symptom,
                                "remedy": ap.remedy,
                            }
                        )

    return SkillExecutionGuidance(
        task=task,
        selected_skills=tuple(selected_skills),
        execution_pipeline=tuple(execution_pipeline),
        stages=tuple(stages),
        active_anti_patterns=tuple(anti_patterns),
        confidence=confidence,
    )


def export_html_brief(registry: Any, output_path: str | None = None) -> str:
    """Generate and save interactive HTML visual brief synchronously."""
    from harness.services.skill_visualizer import SkillGraphVisualizer

    return SkillGraphVisualizer.render_html(registry, output_path=output_path)


__all__ = [
    "compile_execution_guidance_plan",
    "export_html_brief",
]
