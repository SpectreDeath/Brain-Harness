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


# --- Click CLI adapters ---
import json
import click


@click.command("assess-compute")
@click.argument("prompt")
@click.option("--files", "-f", "files_count", default=1, type=int, help="Number of files in target task scope")
@click.option("--arch", "-a", "is_architecture", is_flag=True, help="Mark task as architectural refactoring")
@click.option("--debug-task", "-d", "is_debugging", is_flag=True, help="Mark task as debugging / diagnostic investigation")
@click.option("--profile", "-p", "profile", type=click.Choice(["balanced", "reasoning_heavy", "cost_optimized", "latency_optimized"]), default="balanced", help="Scoring profile heuristic preset")
@click.option("--override", "-o", "override_tier", type=click.Choice(["high_reasoning", "standard_agentic", "fast_mechanical", "high", "medium", "low"]), default=None, help="Force specific model tier override")
@click.option("--json", "output_json", is_flag=True, help="Output raw assessment in JSON format")
@click.option("--html", "generate_html", is_flag=True, help="Generate interactive HTML visual review brief in %TEMP%")
def assess_compute_cli(
    prompt: str,
    files_count: int,
    is_architecture: bool,
    is_debugging: bool,
    profile: str,
    override_tier: str | None,
    output_json: bool,
    generate_html: bool,
) -> None:
    """Assess task surface complexity and recommend optimal model tier & reasoning budget."""
    res = assess_compute_cmd(
        prompt,
        files_count=files_count,
        is_architecture=is_architecture,
        is_debugging=is_debugging,
        override_tier=override_tier,
        profile=profile,
        generate_html=generate_html,
        task_title="CLI Compute Assessment",
    )

    if output_json:
        click.echo(json.dumps(res.assessment.to_dict(), indent=2))
        return

    if generate_html and res.html_path:
        click.echo(f"\n✓ Generated Interactive HTML Visual Brief: {res.html_path}")

    click.echo("\n" + res.recommendation_block)


__all__ = [
    "ComputeAssessmentResult",
    "assess_compute_cli",
    "assess_compute_cmd",
]
