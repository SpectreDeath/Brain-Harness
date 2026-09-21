"""BigQuery Augmented Analytics service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class TemporalTrendPointData(BaseModel):
    """Individual trend point with stripped noise."""

    date: str = Field(..., description="Date or timestamp string")
    value: float = Field(..., description="Observed raw value")
    trend: float = Field(..., description="Decomposed trend trajectory value")
    noise: float = Field(..., description="Residual noise value")


class SeasonalityCycleData(BaseModel):
    """Recurring periodicity cycle."""

    period_name: str = Field(..., description="Name of seasonal cycle (e.g. WEEKLY, MONTHLY)")
    strength: float = Field(..., description="Relative strength weight 0.0 to 1.0")
    dominant: bool = Field(default=False, description="Whether this is the dominant cycle")


class TemporalProfileData(BaseModel):
    """Stage 1: Temporal profiling separating trend from noise and seasonality."""

    table: str = Field(..., description="Target table identifier")
    metric_col: str = Field(..., description="Target metric column")
    timestamp_col: str = Field(..., description="Timestamp column")
    trend_slope: float = Field(default=0.0, description="Overall trend slope")
    noise_variance: float = Field(default=0.0, description="Variance of residual noise")
    seasonal_cycles: list[SeasonalityCycleData] = Field(default_factory=list, description="Seasonal cycles")
    trend_points: list[TemporalTrendPointData] = Field(default_factory=list, description="Trend points")
    sql_query: str = Field(..., description="Executed BigQuery SQL query")


class ChangePointItemData(BaseModel):
    """Statistically significant step change point."""

    start_time: str = Field(..., description="Shift start timestamp")
    end_time: str = Field(..., description="Shift end timestamp")
    mean: float = Field(..., description="Post-shift mean value")
    variance: float = Field(..., description="Post-shift variance")
    change_point_prob: float = Field(..., description="Bayesian change-point probability")


class ChangePointsData(BaseModel):
    """Stage 2: Persistent regime shift change points."""

    table: str = Field(..., description="Target table identifier")
    metric_col: str = Field(..., description="Target metric column")
    timestamp_col: str = Field(..., description="Timestamp column")
    change_points: list[ChangePointItemData] = Field(default_factory=list, description="Detected change points")
    primary_shift_t0: str | None = Field(default=None, description="Primary isolated shift timestamp t0")
    reference_interval: list[str] | None = Field(default=None, description="Reference baseline interval")
    interest_interval: list[str] | None = Field(default=None, description="Interest cohort interval")
    max_probability: float = Field(default=0.0, description="Highest change point probability")
    sql_query: str = Field(..., description="Executed BigQuery SQL query")


class DriverSegmentItemData(BaseModel):
    """Combinatorial dimension segment identified via Apriori rule mining."""

    segment: str = Field(..., description="Segment definition expression")
    metric_delta: float = Field(..., description="Absolute delta contribution")
    percentage_change: float = Field(..., description="Percentage lift")
    segment_contribution: float = Field(..., description="Fraction of cohort variance explained")
    dimension_values: dict[str, str] = Field(default_factory=dict, description="Dimension mapping")


class KeyDriversData(BaseModel):
    """Stage 3: Multi-dimensional driver segments explaining cohort delta."""

    table: str = Field(..., description="Target table identifier")
    metric_col: str = Field(..., description="Target metric column")
    dimension_cols: list[str] = Field(default_factory=list, description="Scanned dimension columns")
    interest_label_col: str = Field(default="is_interest_period", description="Label column for interest cohort")
    min_apriori_support: float = Field(default=0.01, description="Apriori support threshold")
    top_k: int = Field(default=20, description="Top K segments limit")
    drivers: list[DriverSegmentItemData] = Field(default_factory=list, description="Identified drivers")
    sql_query: str = Field(..., description="Executed BigQuery SQL query")


class CausalTrajectoryPointData(BaseModel):
    """Time-series point comparing actual vs counterfactual control."""

    date: str = Field(..., description="Date string")
    actual: float = Field(..., description="Observed actual volume")
    counterfactual: float = Field(..., description="Synthetic counterfactual baseline")
    lower_bound: float = Field(..., description="Confidence lower bound")
    upper_bound: float = Field(..., description="Confidence upper bound")


class CausalEffectData(BaseModel):
    """Stage 4: Synthetic counterfactual modeling via ARIMA_PLUS."""

    table: str = Field(..., description="Target table identifier")
    data_col: str = Field(..., description="Target data column")
    timestamp_col: str = Field(..., description="Timestamp column")
    intervention_timestamp: str = Field(..., description="Intervention timestamp t0")
    actual: float = Field(..., description="Cumulative observed volume")
    counterfactual_baseline: float = Field(..., description="Synthetic control baseline")
    absolute_effect: float = Field(..., description="True incremental causal lift")
    relative_effect: float = Field(..., description="Percentage causal lift")
    prob_causal_effect: float = Field(..., description="Bayesian probability of causal effect")
    trajectory_points: list[CausalTrajectoryPointData] = Field(default_factory=list, description="Trajectory")
    sql_query: str = Field(..., description="Executed BigQuery SQL query")


class ExecutiveDiagnosticNarrativeData(BaseModel):
    """Stage 5: 4-Point diagnostic executive narrative."""

    when: str = Field(..., description="Shift timestamp and persistence duration")
    what: str = Field(..., description="Magnitude of delta and decomposed trend")
    who: str = Field(..., description="Contributing segments and dimensions")
    impact: str = Field(..., description="True causal lift over counterfactual baseline")
    recommendation: str = Field(..., description="Strategic business recommendation")


class AugmentedInvestigationData(BaseModel):
    """Comprehensive 5-stage augmented analytics investigation report."""

    target_table: str = Field(..., description="Audited BigQuery table")
    metric_col: str = Field(..., description="Analyzed metric column")
    timestamp_col: str = Field(..., description="Timestamp column")
    dimension_cols: list[str] = Field(default_factory=list, description="Audited dimension columns")
    temporal_profile: TemporalProfileData
    change_points: ChangePointsData
    key_drivers: KeyDriversData
    causal_effect: CausalEffectData
    narrative: ExecutiveDiagnosticNarrativeData
    estimated_bytes_scanned: int = Field(default=0, description="Estimated byte scan count")
    dry_run: bool = Field(default=False, description="Whether query was executed in dry-run mode")
    timestamp: str = Field(..., description="ISO 8601 execution timestamp")


@runtime_checkable
class BigQueryAugmentedAnalyticsService(Protocol):
    """Protocol for BigQuery in-database augmented analytics TVF execution."""

    def profile_temporal(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        seasonalities: list[str] | None = None,
        mock_data: dict[str, Any] | None = None,
    ) -> TemporalProfileData | Any:
        """Execute Stage 1 Temporal Profiling via ML.TREND and ML.SEASONALITY."""
        ...

    def detect_change_points(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        min_probability: float = 0.95,
        mock_data: dict[str, Any] | None = None,
    ) -> ChangePointsData | Any:
        """Execute Stage 2 Structural Shift Isolation via ML.DETECT_CHANGE_POINTS."""
        ...

    def attribute_drivers(
        self,
        table: str,
        metric_col: str,
        dimension_cols: list[str],
        interest_condition: str,
        min_apriori_support: float = 0.01,
        top_k: int = 20,
        mock_data: dict[str, Any] | None = None,
    ) -> KeyDriversData | Any:
        """Execute Stage 3 Combinatorial Attribution via AI.KEY_DRIVERS."""
        ...

    def estimate_causal_lift(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        intervention_timestamp: str,
        output_time_series: bool = True,
        mock_data: dict[str, Any] | None = None,
    ) -> CausalEffectData | Any:
        """Execute Stage 4 Counterfactual Impact Modeling via AI.CAUSAL_EFFECT."""
        ...

    def run_investigation(
        self,
        target_table: str,
        metric_col: str,
        timestamp_col: str,
        dimension_cols: list[str],
        intervention_timestamp: str | None = None,
        min_apriori_support: float = 0.01,
        top_k: int = 20,
        mock_data: dict[str, Any] | None = None,
    ) -> AugmentedInvestigationData | Any:
        """Run complete 5-stage investigative pipeline end-to-end."""
        ...

    def visual_brief(
        self,
        investigation_result: Any,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Tailwind and Mermaid."""
        ...


BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY: ServiceKey[BigQueryAugmentedAnalyticsService] = (
    ServiceKey("service.bigquery_augmented_analytics")
)
