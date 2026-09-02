"""Dynamic reasoning budget and model tier escalation engine for multi-attempt agent loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harness.services.compute.types import (
    GLOBAL_PRICING_CATALOG,
    AssessmentTrace,
    ComplexityVector,
    ComputeAssessment,
    ComputeEconomicsEstimator,
    ModelPricingCatalog,
    ModelTier,
    ThinkingBudget,
)


@dataclass
class TrajectoryState:
    """State tracking for a task execution trajectory across attempts and errors."""

    attempt_count: int = 1
    error_count: int = 0
    consecutive_failures: int = 0
    total_tokens_consumed: int = 0
    is_escalated: bool = False
    original_tier: ModelTier = ModelTier.STANDARD_AGENTIC
    current_tier: ModelTier = ModelTier.STANDARD_AGENTIC
    history: list[dict[str, Any]] = field(default_factory=list)

    def record_attempt(self, success: bool, error: str | None = None, tokens_used: int = 0) -> None:
        """Record the outcome of an execution attempt."""
        self.attempt_count += 1
        self.total_tokens_consumed += tokens_used
        if not success:
            self.error_count += 1
            self.consecutive_failures += 1
            self.history.append({"attempt": self.attempt_count - 1, "status": "failed", "error": error})
        else:
            self.consecutive_failures = 0
            self.history.append({"attempt": self.attempt_count - 1, "status": "success"})


class DynamicTrajectoryEscalator:
    """Dynamic reasoning budget and model tier escalation engine for multi-attempt agent loops."""

    @classmethod
    def escalate(
        cls,
        base_assessment: ComputeAssessment,
        trajectory: TrajectoryState,
        *,
        catalog: ModelPricingCatalog | None = None,
    ) -> ComputeAssessment:
        """Dynamically escalate thinking budget and model tier based on trajectory failures/retries."""
        if trajectory.error_count == 0 and trajectory.consecutive_failures == 0 and trajectory.attempt_count <= 1:
            return base_assessment

        active_catalog = catalog or GLOBAL_PRICING_CATALOG
        tier = base_assessment.model_tier
        complexity = base_assessment.complexity
        budget = base_assessment.budget_tokens
        thinking = base_assessment.thinking_level
        rec_model = base_assessment.recommended_model
        alts = list(base_assessment.alternative_models)
        reason_notes: list[str] = []

        if trajectory.consecutive_failures >= 2 or (tier == ModelTier.HIGH_REASONING and trajectory.error_count >= 1):
            # Max thinking escalation
            complexity = "High"
            tier = ModelTier.HIGH_REASONING
            thinking = ThinkingBudget.HIGH
            rec_model = "gemini-3.7-flash"
            budget = max(budget * 2, 24576)
            alts = ["claude-3-7-sonnet", "o3-mini", "o1", "deepseek-r1"]
            reason_notes.append(f"Escalated to MAX reasoning budget ({budget:,} tokens) after {trajectory.consecutive_failures} consecutive failures.")
        elif trajectory.consecutive_failures >= 1 or trajectory.error_count >= 1 or trajectory.attempt_count > 1:
            if tier == ModelTier.FAST_MECHANICAL:
                complexity = "Medium"
                tier = ModelTier.STANDARD_AGENTIC
                thinking = ThinkingBudget.MEDIUM
                rec_model = "gemini-3.7-flash"
                budget = 4096
                alts = ["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"]
                reason_notes.append("Escalated from FAST_MECHANICAL to STANDARD_AGENTIC after error/retry.")
            elif tier == ModelTier.STANDARD_AGENTIC:
                complexity = "High"
                tier = ModelTier.HIGH_REASONING
                thinking = ThinkingBudget.HIGH
                rec_model = "gemini-3.7-flash"
                budget = 16384
                alts = ["claude-3-7-sonnet", "o3-mini", "deepseek-r1"]
                reason_notes.append("Escalated from STANDARD_AGENTIC to HIGH_REASONING after error/retry.")

        trajectory.is_escalated = True
        trajectory.current_tier = tier

        econ = ComputeEconomicsEstimator.estimate(rec_model, thinking, budget, catalog=active_catalog)
        escalated_vector = base_assessment.vector
        if escalated_vector:
            escalated_vector = ComplexityVector(
                ambiguity_score=min(1.0, escalated_vector.ambiguity_score + 0.2),
                span_score=escalated_vector.span_score,
                depth_score=min(1.0, escalated_vector.depth_score + 0.2),
                rigor_score=min(1.0, escalated_vector.rigor_score + 0.2),
                concurrency_score=escalated_vector.concurrency_score,
                composite_score=min(1.0, escalated_vector.composite_score + 0.2),
                level=complexity,
            )

        escalated_trace = base_assessment.trace
        if escalated_trace:
            escalated_trace = AssessmentTrace(
                high_factors=escalated_trace.high_factors + reason_notes,
                low_factors=escalated_trace.low_factors,
                detected_keywords=escalated_trace.detected_keywords,
                files_evaluated=escalated_trace.files_evaluated,
                is_architectural=escalated_trace.is_architectural,
                is_debugging=True,
                profile_used=escalated_trace.profile_used,
                notes=f"Trajectory escalated: {' '.join(reason_notes)}",
            )

        return ComputeAssessment(
            complexity=complexity,
            model_tier=tier,
            thinking_level=thinking,
            recommended_model=rec_model,
            budget_tokens=budget,
            alternative_models=alts,
            reasoning=base_assessment.reasoning + " " + " ".join(reason_notes),
            vector=escalated_vector,
            trace=escalated_trace,
            economics=econ,
        )

    @classmethod
    def allocate_tree_budget(
        cls,
        total_budget_tokens: int,
        branch_weights: list[float],
    ) -> list[int]:
        """Proportionally allocate reasoning token budget across swarm/tree branches."""
        if not branch_weights:
            return []
        total_weight = sum(branch_weights)
        if total_weight <= 0:
            equal_share = total_budget_tokens // len(branch_weights)
            return [equal_share] * len(branch_weights)
        return [int((w / total_weight) * total_budget_tokens) for w in branch_weights]
