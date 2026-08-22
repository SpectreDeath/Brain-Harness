"""Critic Loop & Iterative Refinement Plugin for Brain Harness.

Coordinates multi-turn generate -> critique -> revise loops using available
evaluators and LLM services to maximize final artifact quality.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

CRITIC_LOOP_KEY: ServiceKey[CriticLoopService] = ServiceKey("agent.critic_loop")


def evaluate_rubric(content: str, rubric: list[str]) -> dict[str, Any]:
    """Score a content output against a rubric checklist."""
    scores: list[dict[str, Any]] = []
    total_score = 0.0

    for item in rubric:
        item_lower = item.lower()
        score = 0.5  # baseline
        reasons: list[str] = []

        # Heuristic checks
        if "type" in item_lower or "typing" in item_lower:
            has_types = bool(re.search(r":\s*[a-zA-Z0-9_|\[\]]+\b|->\s*[a-zA-Z0-9_|\[\]]+", content))
            score = 1.0 if has_types else 0.3
            reasons.append("Type annotations verified" if has_types else "Missing explicit type annotations")
        elif "docstring" in item_lower or "documentation" in item_lower or "comment" in item_lower:
            has_docs = '"""' in content or "'''" in content or "#" in content
            score = 1.0 if has_docs else 0.4
            reasons.append("Docstrings present" if has_docs else "Missing docstrings / comments")
        elif "error" in item_lower or "exception" in item_lower or "try" in item_lower:
            has_err_handling = "try:" in content or "except" in content or "raise" in content
            score = 1.0 if has_err_handling else 0.4
            reasons.append("Error handling verified" if has_err_handling else "No exception handling detected")
        elif "clean" in item_lower or "style" in item_lower:
            lines = content.splitlines()
            long_lines = sum(1 for ln in lines if len(ln) > 120)
            score = max(0.2, 1.0 - (long_lines * 0.1))
            reasons.append(f"Line length acceptable ({long_lines} long lines)" if long_lines == 0 else f"{long_lines} lines exceed 120 chars")
        else:
            # Token match check
            tokens = [t for t in re.findall(r"\w+", item_lower) if len(t) > 3]
            matches = sum(1 for t in tokens if t in content.lower())
            ratio = matches / len(tokens) if tokens else 0.5
            score = min(1.0, 0.4 + (ratio * 0.6))
            reasons.append(f"Keyword alignment: {int(ratio * 100)}%")

        scores.append({
            "criterion": item,
            "score": round(score, 2),
            "feedback": "; ".join(reasons),
        })
        total_score += score

    overall = total_score / len(rubric) if rubric else 1.0
    return {
        "overall_score": round(overall, 2),
        "criteria_count": len(rubric),
        "breakdown": scores,
        "passed": overall >= 0.80,
    }


async def run_critic_loop(
    task: str,
    draft: str,
    *,
    rubric: list[str] | None = None,
    max_iterations: int = 3,
    threshold: float = 0.85,
    llm_service: Any | None = None,
) -> dict[str, Any]:
    """Iteratively evaluate and refine a draft until threshold score is reached."""
    active_rubric = rubric or [
        "Include strict type annotations on all function signatures",
        "Provide clear docstrings with parameters and return descriptions",
        "Implement robust error handling and input validation",
        "Adhere to clean code style without bloated lines",
    ]

    current_draft = draft
    trajectory: list[dict[str, Any]] = []

    for step in range(1, max_iterations + 1):
        eval_result = evaluate_rubric(current_draft, active_rubric)
        score = eval_result["overall_score"]

        trajectory.append({
            "iteration": step,
            "score": score,
            "passed": eval_result["passed"],
            "feedback": [b["feedback"] for b in eval_result["breakdown"] if b["score"] < 0.8],
        })

        if score >= threshold:
            logger.info("Critic loop converged", iteration=step, score=score)
            break

        # Simulate or perform refinement
        if llm_service is not None and hasattr(llm_service, "generate"):
            try:
                feedback_str = "\n".join(trajectory[-1]["feedback"])
                prompt = (
                    f"Task: {task}\n\n"
                    f"Current Draft:\n{current_draft}\n\n"
                    f"Critic Feedback:\n{feedback_str}\n\n"
                    f"Please provide an improved revision addressing all feedback:"
                )
                refined = await llm_service.generate(prompt)
                if refined:
                    current_draft = str(refined)
            except Exception as e:
                logger.warning("LLM refinement step failed", step=step, error=str(e))
                break

    final_eval = evaluate_rubric(current_draft, active_rubric)
    return {
        "status": "ok",
        "task": task,
        "iterations_completed": len(trajectory),
        "initial_score": trajectory[0]["score"] if trajectory else 0.0,
        "final_score": final_eval["overall_score"],
        "converged": final_eval["overall_score"] >= threshold,
        "trajectory": trajectory,
        "final_draft": current_draft,
    }


class CriticLoopService:
    """Service facade for critic loops."""

    def evaluate(self, content: str, rubric: list[str]) -> dict[str, Any]:
        return evaluate_rubric(content, rubric)

    async def refine(
        self,
        task: str,
        draft: str,
        *,
        rubric: list[str] | None = None,
        max_iterations: int = 3,
        threshold: float = 0.85,
        llm_service: Any | None = None,
    ) -> dict[str, Any]:
        return await run_critic_loop(
            task=task,
            draft=draft,
            rubric=rubric,
            max_iterations=max_iterations,
            threshold=threshold,
            llm_service=llm_service,
        )


class CriticLoopPlugin(HarnessPlugin):
    """Plugin providing generate-critique-revise iterative loops."""

    @property
    def name(self) -> str:
        return "plugin.critic_loop"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Autonomous generate-critique-revise loop with rubric scoring and iterative refinement"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CRITIC_LOOP_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CRITIC_LOOP_KEY, CriticLoopService(), provider=self.name)
        logger.info("CriticLoopService provided", plugin=self.name)
