"""Multi-turn iterative critique, LLM revision, and convergence tracking."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any
import structlog

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)


async def run_refinement_loop(
    eval_fn: Callable[[str, list[str]], dict[str, Any]],
    task: str,
    draft: str,
    *,
    rubric: list[str] | None = None,
    max_iterations: int = 3,
    threshold: float = 0.85,
    llm_service: Any | None = None,
) -> dict[str, Any]:
    """Run iterative multi-turn critique and refinement until threshold is achieved."""
    active_rubric = rubric or [
        "Include strict type annotations on all function signatures",
        "Provide clear docstrings with parameters and return descriptions",
        "Implement robust error handling and input validation",
        "Adhere to clean code style without bloated lines",
    ]

    current_draft = draft
    trajectory: list[dict[str, Any]] = []

    for step in range(1, max_iterations + 1):
        eval_result = eval_fn(current_draft, active_rubric)
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

    final_eval = eval_fn(current_draft, active_rubric)
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


__all__ = ["run_refinement_loop"]
