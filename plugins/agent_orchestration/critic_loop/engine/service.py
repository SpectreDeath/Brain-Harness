"""Consolidated implementation of CriticEvaluationService."""

from __future__ import annotations

import sys
from typing import Any

from plugins.agent_orchestration.critic_loop.engine.code_ast import evaluate_code_ast
from plugins.agent_orchestration.critic_loop.engine.debate import (
    conduct_dialectical_debate,
    synthesize_debate_verdict,
)
from plugins.agent_orchestration.critic_loop.engine.plan import review_plan_feasibility
from plugins.agent_orchestration.critic_loop.engine.refinement import run_refinement_loop
from plugins.agent_orchestration.critic_loop.engine.rubric import evaluate_rubric
from plugins.agent_orchestration.critic_loop.engine.safety import check_command_safety

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class CriticEvaluationServiceImpl:
    """Consolidated implementation of the Critic & Safety Evaluation Gate."""

    def evaluate(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Unified evaluation entrypoint alias delegating to evaluate_rubric."""
        return self.evaluate_rubric(content, rubric)

    def evaluate_rubric(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Score content against a criteria checklist with breakdown."""
        return evaluate_rubric(content, rubric)

    def check_command_safety(self, command: str) -> dict[str, Any]:
        """Scan shell commands for dangerous or irreversible operations."""
        return check_command_safety(command)

    def evaluate_code_ast(self, code: str, language: str = "python") -> dict[str, Any]:
        """Statically inspect syntax, AST complexity, and anti-patterns."""
        return evaluate_code_ast(code, language)

    def review_plan_feasibility(self, goal: str, steps: list[str]) -> dict[str, Any]:
        """Evaluate plan steps for verification steps, risks, and mitigations."""
        return review_plan_feasibility(goal, steps)

    def conduct_dialectical_debate(
        self,
        topic: str,
        pro_arguments: list[str],
        con_arguments: list[str],
    ) -> dict[str, Any]:
        """Orchestrate dialectical argument rounds between Proposer and Challenger."""
        return conduct_dialectical_debate(topic, pro_arguments, con_arguments)

    def synthesize_debate_verdict(self, debate_summary: dict[str, Any]) -> dict[str, Any]:
        """Synthesize an impartial arbiter decision based on debate rounds."""
        return synthesize_debate_verdict(debate_summary)

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
        """Run iterative multi-turn critique and refinement until threshold is achieved."""
        return await run_refinement_loop(
            self.evaluate_rubric,
            task,
            draft,
            rubric=rubric,
            max_iterations=max_iterations,
            threshold=threshold,
            llm_service=llm_service,
        )


_EVAL_INSTANCE = CriticEvaluationServiceImpl()
CriticLoopService = CriticEvaluationServiceImpl

__all__ = [
    "CriticEvaluationServiceImpl",
    "CriticLoopService",
    "_EVAL_INSTANCE",
]
