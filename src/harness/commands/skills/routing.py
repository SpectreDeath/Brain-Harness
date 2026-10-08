"""Intent routing, intelligent selection, guidance compilation, and action interception commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.commands.skills.seams import get_skill_registry


def route_skills_cmd(
    intent: str,
    top_k: int = 3,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    registry = get_skill_registry(root_path, context=context)
    return registry.route_intent(intent, top_k=top_k)


def select_skills_cmd(
    task: str,
    max_skills: int = 5,
    include_verifier: bool = True,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Select skills and compile an intelligent topological execution plan for an agent task."""
    registry = get_skill_registry(root_path, context=context)
    plan = registry.select_skills_for_task(
        task=task, max_skills=max_skills, include_verifier=include_verifier
    )
    return {
        "status": "ok",
        "plan": plan.model_dump(),
    }


def compile_guidance_cmd(
    task: str,
    max_skills: int = 4,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Compile end-to-end execution guidance plan for an agent task."""
    registry = get_skill_registry(root_path, context=context)
    guidance = registry.compile_execution_guidance(task=task, max_skills=max_skills)
    return {
        "status": "ok",
        "task": guidance.task,
        "selected_skills": list(guidance.selected_skills),
        "execution_pipeline": list(guidance.execution_pipeline),
        "stages": list(guidance.stages),
        "active_anti_patterns": list(guidance.active_anti_patterns),
        "confidence": guidance.confidence,
        "prompt_block": guidance.format_system_prompt_block(),
    }


def intercept_action_cmd(
    action_name: str,
    action_input: dict[str, Any],
    active_skills: list[str] | tuple[str, ...] | None = None,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Intercept proposed tool action and arguments against anti-patterns and AST gates."""
    from harness.services.skill_graph import AntiPatternGuard

    registry = get_skill_registry(root_path, context=context)
    skills_list = list(active_skills) if active_skills else None
    violations = registry.intercept_action(
        action_name=action_name,
        action_input=action_input,
        active_skills=skills_list,
    )
    obs = AntiPatternGuard.format_self_repair_observation(violations)
    return {
        "status": obs.get("status", "ok"),
        "violations": [v.model_dump() for v in violations],
        "observation": obs,
        "action_name": action_name,
    }
