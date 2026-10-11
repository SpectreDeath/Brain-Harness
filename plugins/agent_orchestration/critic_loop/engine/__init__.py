"""Critic Loop evaluation and dialectical debate engine package."""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from plugins.agent_orchestration.critic_loop.engine.code_ast import evaluate_code_ast
from plugins.agent_orchestration.critic_loop.engine.debate import (
    conduct_dialectical_debate,
    synthesize_debate_verdict,
)
from plugins.agent_orchestration.critic_loop.engine.models import (
    CRITIC_EVALUATION_SERVICE_KEY,
    CRITIC_LOOP_KEY,
    CommandSafetyReport,
    CriticEvaluationService,
    DebateRound,
    RubricCriterionScore,
    RubricScoreReport,
    _DANGEROUS_PATTERNS,
)
from plugins.agent_orchestration.critic_loop.engine.plan import review_plan_feasibility
from plugins.agent_orchestration.critic_loop.engine.refinement import run_refinement_loop
from plugins.agent_orchestration.critic_loop.engine.rubric import evaluate_rubric
from plugins.agent_orchestration.critic_loop.engine.safety import check_command_safety
from plugins.agent_orchestration.critic_loop.engine.service import (
    CriticEvaluationServiceImpl,
    CriticLoopService,
    _EVAL_INSTANCE,
)

__all__ = [
    "CRITIC_EVALUATION_SERVICE_KEY",
    "CRITIC_LOOP_KEY",
    "CommandSafetyReport",
    "CriticEvaluationService",
    "CriticEvaluationServiceImpl",
    "CriticLoopService",
    "DebateRound",
    "RubricCriterionScore",
    "RubricScoreReport",
    "_DANGEROUS_PATTERNS",
    "_EVAL_INSTANCE",
    "check_command_safety",
    "conduct_dialectical_debate",
    "evaluate_code_ast",
    "evaluate_rubric",
    "review_plan_feasibility",
    "run_refinement_loop",
    "synthesize_debate_verdict",
]
