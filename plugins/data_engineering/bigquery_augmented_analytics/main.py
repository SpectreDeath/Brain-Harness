"""BigQuery Augmented Analytics Plugin — In-Database TVF Execution Seam."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts directory and src are on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "bigquery-augmented-analytics" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from bigquery_augmented_analytics import BigQueryAugmentedAnalyticsEngine

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.bigquery_augmented_analytics import (
    BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY,
    AugmentedInvestigationData,
    BigQueryAugmentedAnalyticsService,
    CausalEffectData,
    ChangePointsData,
    KeyDriversData,
    TemporalProfileData,
)

logger = structlog.get_logger(__name__)


class BigQueryAugmentedAnalyticsPlugin(HarnessPlugin, BigQueryAugmentedAnalyticsService):
    """Plugin providing in-database BigQuery TVF execution for anomalies, attribution, and causal lift."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = BigQueryAugmentedAnalyticsEngine()

    @property
    def name(self) -> str:
        return "plugin.bigquery_augmented_analytics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "BigQuery in-database augmented analytics TVF execution for anomaly detection, "
            "change point isolation, Apriori attribution, and ARIMA_PLUS causal lift"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the BigQueryAugmentedAnalyticsService into the IoC container."""
        context.provide(BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY, self)
        logger.info(
            "bigquery_augmented_analytics_service_provided",
            service=str(BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- BigQueryAugmentedAnalyticsService Implementation ---

    def profile_temporal(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        seasonalities: list[str] | None = None,
        mock_data: dict[str, Any] | None = None,
    ) -> TemporalProfileData:
        """Execute Stage 1 Temporal Profiling via ML.TREND and ML.SEASONALITY."""
        res = self._engine.profile_temporal(
            table=table,
            data_col=data_col,
            timestamp_col=timestamp_col,
            seasonalities=seasonalities,
            mock_data=mock_data,
        )
        return TemporalProfileData.model_validate(res.to_dict())

    def detect_change_points(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        min_probability: float = 0.95,
        mock_data: dict[str, Any] | None = None,
    ) -> ChangePointsData:
        """Execute Stage 2 Structural Shift Isolation via ML.DETECT_CHANGE_POINTS."""
        res = self._engine.detect_change_points(
            table=table,
            data_col=data_col,
            timestamp_col=timestamp_col,
            min_probability=min_probability,
            mock_data=mock_data,
        )
        return ChangePointsData.model_validate(res.to_dict())

    def attribute_drivers(
        self,
        table: str,
        metric_col: str,
        dimension_cols: list[str],
        interest_condition: str,
        min_apriori_support: float = 0.01,
        top_k: int = 20,
        mock_data: dict[str, Any] | None = None,
    ) -> KeyDriversData:
        """Execute Stage 3 Combinatorial Attribution via AI.KEY_DRIVERS."""
        res = self._engine.attribute_key_drivers(
            table=table,
            metric_col=metric_col,
            dimension_cols=dimension_cols,
            interest_condition=interest_condition,
            min_apriori_support=min_apriori_support,
            top_k=top_k,
            mock_data=mock_data,
        )
        return KeyDriversData.model_validate(res.to_dict())

    def estimate_causal_lift(
        self,
        table: str,
        data_col: str,
        timestamp_col: str,
        intervention_timestamp: str,
        output_time_series: bool = True,
        mock_data: dict[str, Any] | None = None,
    ) -> CausalEffectData:
        """Execute Stage 4 Counterfactual Impact Modeling via AI.CAUSAL_EFFECT."""
        res = self._engine.estimate_causal_effect(
            table=table,
            data_col=data_col,
            timestamp_col=timestamp_col,
            intervention_timestamp=intervention_timestamp,
            output_time_series=output_time_series,
            mock_data=mock_data,
        )
        return CausalEffectData.model_validate(res.to_dict())

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
    ) -> AugmentedInvestigationData:
        """Run complete 5-stage investigative pipeline end-to-end."""
        res = self._engine.run_investigative_pipeline(
            target_table=target_table,
            metric_col=metric_col,
            timestamp_col=timestamp_col,
            dimension_cols=dimension_cols,
            intervention_timestamp=intervention_timestamp,
            min_apriori_support=min_apriori_support,
            top_k=top_k,
            mock_data=mock_data,
        )
        return AugmentedInvestigationData.model_validate(res.to_dict())

    def visual_brief(
        self,
        investigation_result: Any,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Tailwind and Mermaid."""
        raw_result = investigation_result
        if hasattr(investigation_result, "model_dump"):
            # If Pydantic model passed, reconstruct slotted engine result
            raw_dict = investigation_result.model_dump()
            raw_result = self._engine.run_investigative_pipeline(
                target_table=raw_dict["target_table"],
                metric_col=raw_dict["metric_col"],
                timestamp_col=raw_dict["timestamp_col"],
                dimension_cols=raw_dict["dimension_cols"],
                mock_data=raw_dict,
            )
        elif not hasattr(raw_result, "target_table"):
            # Fallback to default simulation
            raw_result = self._engine.run_investigative_pipeline(
                target_table="sample.metrics",
                metric_col="trips",
                timestamp_col="date",
                dimension_cols=["type", "region"],
            )
        return self._engine.generate_visual_brief(raw_result, output_path=output_path)


# Rule 45: Export module singleton plugin instance
plugin = BigQueryAugmentedAnalyticsPlugin()


# Top-level tool functions matching plugin.json entrypoints
def bigquery_temporal_profile(
    table: str,
    data_col: str,
    timestamp_col: str,
    seasonalities: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute Stage 1 Temporal Profiling via ML.TREND and ML.SEASONALITY."""
    report = plugin.profile_temporal(
        table=table,
        data_col=data_col,
        timestamp_col=timestamp_col,
        seasonalities=seasonalities,
    )
    return report.model_dump()


def bigquery_detect_change_points(
    table: str,
    data_col: str,
    timestamp_col: str,
    min_probability: float = 0.95,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute Stage 2 Structural Shift Isolation via ML.DETECT_CHANGE_POINTS."""
    report = plugin.detect_change_points(
        table=table,
        data_col=data_col,
        timestamp_col=timestamp_col,
        min_probability=min_probability,
    )
    return report.model_dump()


def bigquery_attribute_drivers(
    table: str,
    metric_col: str,
    dimension_cols: list[str],
    interest_condition: str,
    min_apriori_support: float = 0.01,
    top_k: int = 20,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute Stage 3 Combinatorial Attribution via AI.KEY_DRIVERS."""
    report = plugin.attribute_drivers(
        table=table,
        metric_col=metric_col,
        dimension_cols=dimension_cols,
        interest_condition=interest_condition,
        min_apriori_support=min_apriori_support,
        top_k=top_k,
    )
    return report.model_dump()


def bigquery_causal_lift(
    table: str,
    data_col: str,
    timestamp_col: str,
    intervention_timestamp: str,
    output_time_series: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute Stage 4 Counterfactual Impact Modeling via AI.CAUSAL_EFFECT."""
    report = plugin.estimate_causal_lift(
        table=table,
        data_col=data_col,
        timestamp_col=timestamp_col,
        intervention_timestamp=intervention_timestamp,
        output_time_series=output_time_series,
    )
    return report.model_dump()


def bigquery_augmented_pipeline(
    table: str,
    metric_col: str,
    timestamp_col: str,
    dimension_cols: list[str],
    intervention_timestamp: str | None = None,
    min_apriori_support: float = 0.01,
    top_k: int = 20,
    dry_run: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute complete 5-Stage BigQuery Augmented Analytics pipeline end-to-end."""
    report = plugin.run_investigation(
        target_table=table,
        metric_col=metric_col,
        timestamp_col=timestamp_col,
        dimension_cols=dimension_cols,
        intervention_timestamp=intervention_timestamp,
        min_apriori_support=min_apriori_support,
        top_k=top_k,
        mock_data={} if dry_run else None,
    )
    return report.model_dump()


def bigquery_visual_brief(
    table: str = "sample_table",
    metric_col: str = "metric_val",
    timestamp_col: str = "date_val",
    dimension_cols: list[str] | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Generate interactive HTML visual brief with Tailwind and Mermaid."""
    dims = dimension_cols or ["dim_a", "dim_b"]
    report = plugin.run_investigation(
        target_table=table,
        metric_col=metric_col,
        timestamp_col=timestamp_col,
        dimension_cols=dims,
    )
    brief_path = plugin.visual_brief(report, output_path=output_path)
    return str(brief_path)
