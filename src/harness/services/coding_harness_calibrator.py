"""CodingHarnessCalibrator service protocol, typed models, and ServiceKey.

Elevates the empirical component-level harness calibration engine (Fan et al. arXiv:2609.20804v1)
into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class BudgetConfigData(BaseModel):
    """Context window thresholds and token bounds."""

    usable_window: int = Field(default=131072, description="Usable token budget window")
    soft_threshold_ratio: float = Field(
        default=0.60, description="Soft threshold B1 ratio"
    )
    hard_threshold_ratio: float = Field(
        default=0.85, description="Hard threshold B2 ratio"
    )
    recent_window_ratio: float = Field(
        default=0.30, description="Recent verbatim window ratio"
    )
    min_recent_turns: int = Field(
        default=2, description="Minimum turns pinned in recent window"
    )
    b1_tokens: int = Field(
        default=78643, description="Token count triggering M1 elision"
    )
    b2_tokens: int = Field(
        default=111411, description="Token count triggering M3 summary"
    )


class CalibrationRecommendationData(BaseModel):
    """Optimal component-level harness configuration for a model and workload."""

    model_name: str = Field(..., description="Target model name")
    harness_mode: str = Field(..., description="scaffold | balanced | efficiency")
    action_space: str = Field(..., description="predefined_tools | bash_only")
    context_tier: str = Field(..., description="Context management tier: T4")
    enable_planning: bool = Field(
        default=True, description="Whether persistent planning is enabled"
    )
    planning_role: str = Field(
        ...,
        description="accuracy_scaffold | balanced_guidance | stopping_point_controller",
    )
    budget_config: BudgetConfigData = Field(default_factory=BudgetConfigData)
    stuck_warn_threshold: int = Field(default=5, description="Streak warning threshold")
    stuck_kill_threshold: int = Field(
        default=8, description="Streak hard-kill threshold"
    )
    deprecation_flags: list[str] = Field(
        default_factory=list, description="Deprecated machinery flags"
    )


class ContextStagingEventData(BaseModel):
    """Event representation in staged context history."""

    role: str = Field(
        ...,
        description="Event role: system | user | assistant | tool_call | tool_observation",
    )
    content: str = Field(..., description="Message content or observation")
    turn: int = Field(..., description="Turn index")
    token_count: int = Field(..., description="Estimated token count")
    is_bulky: bool = Field(
        default=False, description="Whether observation exceeds bulky threshold"
    )
    tool_name: str = Field(default="", description="Name of tool if tool event")


class ContextStagingSimulationData(BaseModel):
    """Result of Two-Tier Context Staging ($T_4$) simulation."""

    usable_window: int = Field(..., description="Total usable window budget")
    initial_tokens: int = Field(..., description="Token count before staging")
    final_tokens: int = Field(..., description="Token count after staging")
    b1_elision_triggered: bool = Field(
        default=False, description="Whether B1 M1 elision fired"
    )
    b2_summary_triggered: bool = Field(
        default=False, description="Whether B2 M3 summary fired"
    )
    elided_observations_count: int = Field(
        default=0, description="Number of bulky observations elided"
    )
    pruned_tokens_count: int = Field(
        default=0, description="Tokens pruned from context"
    )
    structured_summary: str = Field(
        default="", description="7-heading structured summary if generated"
    )
    events_after_staging: list[ContextStagingEventData] = Field(default_factory=list)


class RepatchPredictionData(BaseModel):
    """Empirical prediction of re-patch churn and cost reductions."""

    model_scale: str = Field(..., description="weak_30b | mid_120b | strong_550b")
    workload: str = Field(..., description="terminal_cli | codebase_repo | mixed")
    action_space: str = Field(..., description="predefined_tools | bash_only")
    predicted_mean_repatches: float = Field(
        ..., description="Predicted mean re-patches per task"
    )
    coarse_replace_ratio: float = Field(
        ..., description="Ratio of coarse create-or-replace actions"
    )
    estimated_cost_reduction_pct: float = Field(
        ..., description="Estimated token cost savings percentage"
    )
    rationale: str = Field(
        ..., description="Empirical rationale grounded in Fan et al."
    )


class HarnessCalibrationReportData(BaseModel):
    """Authoritative aggregate calibration assessment report."""

    recommendation: CalibrationRecommendationData
    repatch_prediction: RepatchPredictionData
    staging_simulation: ContextStagingSimulationData | None = None
    summary_narrative: str = Field(..., description="Narrative evaluation summary")


class StuckDetectionResultData(BaseModel):
    """Result of streak-based stuck monitoring check."""

    action_instruction: str = Field(
        ..., description="none | inject_warning_reminder | terminate_stuck_failures"
    )
    should_terminate: bool = Field(
        default=False, description="Whether execution must be halted"
    )


@runtime_checkable
class CodingHarnessCalibratorService(Protocol):
    """Protocol for empirical coding harness component calibration, staging simulation, and forecasting."""

    def calibrate(
        self,
        model_name: str,
        parameter_billions: float,
        workload: str,
        context_budget: int = 131072,
    ) -> CalibrationRecommendationData | Any:
        """Calibrate mode, action space, planning role, and context budgets."""
        ...

    def simulate_staging(
        self,
        events: list[dict[str, Any]] | list[Any],
        usable_window: int = 131072,
        soft_ratio: float = 0.60,
        hard_ratio: float = 0.85,
    ) -> ContextStagingSimulationData | Any:
        """Simulate Two-Tier Context Staging ($T_4$) over an event sequence."""
        ...

    def predict_repatch(
        self,
        model_capability: str | float,
        action_space: str,
        workload: str,
    ) -> RepatchPredictionData | Any:
        """Predict mean re-patches per task and cost reduction."""
        ...

    def generate_report(
        self,
        model_name: str,
        parameter_billions: float,
        workload: str,
        context_budget: int = 131072,
        events: list[Any] | None = None,
    ) -> HarnessCalibrationReportData | Any:
        """Synthesize aggregate calibration report."""
        ...

    def visual_brief(
        self,
        report_or_rec: Any | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief with Mermaid topology."""
        ...


CODING_HARNESS_CALIBRATOR_SERVICE_KEY: ServiceKey[CodingHarnessCalibratorService] = (
    ServiceKey("service.coding_harness_calibrator")
)
