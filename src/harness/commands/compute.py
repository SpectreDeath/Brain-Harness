"""Compute commands — pure async and sync functions for model tiering and budget routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from harness.services.compute_assessor import ComputeAssessment, ModelTier

logger = structlog.get_logger()


@dataclass
class ComputeAssessmentResult:
    """Outcome of assessing task complexity and compute routing."""

    assessment: ComputeAssessment
    recommendation_block: str
    html_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = self.assessment.to_dict()
        if self.html_path:
            data["html_path"] = self.html_path
        return data


def assess_compute_cmd(
    prompt: str,
    *,
    files_count: int = 1,
    is_architecture: bool = False,
    is_debugging: bool = False,
    profile: str = "balanced",
    override_tier: str | ModelTier | None = None,
    generate_html: bool = False,
    task_title: str = "Compute Assessment",
) -> ComputeAssessmentResult:
    """Assess task complexity and recommend optimal model tier and thinking budget.

    Args:
        prompt: Task description / prompt to evaluate.
        files_count: Estimated count of files in scope.
        is_architecture: Whether task involves architectural refactoring.
        is_debugging: Whether task involves hard debugging / diagnostics.
        profile: Scoring profile heuristic preset.
        override_tier: Optional forced tier override.
        generate_html: Whether to generate an interactive HTML visual brief in %TEMP%.
        task_title: Title for visual brief report.

    Returns:
        ComputeAssessmentResult containing assessment and optional HTML report path.
    """
    from harness.services.compute_assessor import ComputeRouter, ModelTier

    tier_enum = None
    if override_tier:
        if isinstance(override_tier, ModelTier):
            tier_enum = override_tier
        else:
            norm = str(override_tier).lower().strip()
            if norm in ("high", "high_reasoning"):
                tier_enum = ModelTier.HIGH_REASONING
            elif norm in ("low", "fast_mechanical"):
                tier_enum = ModelTier.FAST_MECHANICAL
            elif norm in ("medium", "standard_agentic"):
                tier_enum = ModelTier.STANDARD_AGENTIC

    assessment = ComputeRouter.assess(
        prompt,
        files_count=files_count,
        is_architecture=is_architecture,
        is_debugging=is_debugging,
        override_tier=tier_enum,
        profile=profile,
    )

    rec_block = assessment.format_recommendation_block()
    html_path = None

    if generate_html:
        html_path = ComputeRouter.generate_visual_brief(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile,
            task_title=task_title,
        )

    logger.info(
        "Computed model assessment",
        model_tier=assessment.model_tier.value,
        budget=assessment.thinking_level.value,
    )


    return ComputeAssessmentResult(
        assessment=assessment,
        recommendation_block=rec_block,
        html_path=html_path,
    )


__all__ = [
    "ComputeAssessmentResult",
    "assess_compute_cmd",
]
