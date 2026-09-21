"""BigQuery commands — headless CLI and IoC service seams for in-database augmented analytics.

Provides CLI inspection for:
- Temporal Profiling (ML.TREND / ML.SEASONALITY)
- Structural Shift & Change-Point Isolation (ML.DETECT_CHANGE_POINTS)
- Combinatorial Apriori Attribution (AI.KEY_DRIVERS)
- Counterfactual Causal Lift Modeling (AI.CAUSAL_EFFECT via ARIMA_PLUS)
- 5-Stage Investigative Pipeline & Interactive Visual Briefs
"""

from __future__ import annotations

import json as _json
import sys
import webbrowser
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
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


def get_bigquery_augmented_analytics_service(
    context: ServiceContext | None = None,
) -> BigQueryAugmentedAnalyticsService:
    """Resolve BigQueryAugmentedAnalyticsService from context or fall back to plugin singleton."""
    if context is not None:
        svc = context.optional(BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.data_engineering.bigquery_augmented_analytics.main import (
            plugin as bq_plugin,
        )

        return bq_plugin
    except Exception as exc:
        logger.warning("bigquery_plugin_fallback_failed", error=str(exc))
        # Direct fallback to domain engine adapter
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "bigquery-augmented-analytics"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from bigquery_augmented_analytics import (  # type: ignore
            BigQueryAugmentedAnalyticsEngine,
        )

        class _EngineAdapter:
            def __init__(self) -> None:
                self._engine = BigQueryAugmentedAnalyticsEngine()

            def profile_temporal(self, *args: Any, **kwargs: Any) -> Any:
                res = self._engine.profile_temporal(*args, **kwargs)
                return TemporalProfileData.model_validate(res.to_dict())

            def detect_change_points(self, *args: Any, **kwargs: Any) -> Any:
                res = self._engine.detect_change_points(*args, **kwargs)
                return ChangePointsData.model_validate(res.to_dict())

            def attribute_drivers(self, *args: Any, **kwargs: Any) -> Any:
                res = self._engine.attribute_key_drivers(*args, **kwargs)
                return KeyDriversData.model_validate(res.to_dict())

            def estimate_causal_lift(self, *args: Any, **kwargs: Any) -> Any:
                res = self._engine.estimate_causal_effect(*args, **kwargs)
                return CausalEffectData.model_validate(res.to_dict())

            def run_investigation(self, *args: Any, **kwargs: Any) -> Any:
                res = self._engine.run_investigative_pipeline(*args, **kwargs)
                return AugmentedInvestigationData.model_validate(res.to_dict())

            def visual_brief(self, investigation_result: Any, output_path: Any = None) -> Path:
                if hasattr(investigation_result, "model_dump"):
                    raw_dict = investigation_result.model_dump()
                    res = self._engine.run_investigative_pipeline(
                        target_table=raw_dict["target_table"],
                        metric_col=raw_dict["metric_col"],
                        timestamp_col=raw_dict["timestamp_col"],
                        dimension_cols=raw_dict["dimension_cols"],
                        mock_data=raw_dict,
                    )
                else:
                    res = investigation_result
                return self._engine.generate_visual_brief(res, output_path=output_path)

        return _EngineAdapter()  # type: ignore


# ---------------------------------------------------------------------------
# Click Command Group (Rule 6: Consolidated Single-Source Declaration)
# ---------------------------------------------------------------------------


@click.group("bigquery")
def bigquery_group() -> None:
    """BigQuery in-database augmented analytics TVF execution suite."""
    pass


@bigquery_group.command("profile")
@click.option("--table", required=True, help="Target BigQuery table identifier")
@click.option("--data-col", required=True, help="Metric column name")
@click.option("--timestamp-col", required=True, help="Timestamp column name")
@click.option("--seasonalities", help="Comma-separated seasonality periods (e.g. WEEKLY,MONTHLY)")
@click.option("--dry-run", is_flag=True, help="Output compiled BigQuery TVF SQL without executing")
@click.option("--json", "json_output", is_flag=True, help="Output JSON result")
def profile_cli(
    table: str,
    data_col: str,
    timestamp_col: str,
    seasonalities: str | None,
    dry_run: bool,
    json_output: bool,
) -> None:
    """Stage 1: Temporal profiling via ML.TREND and ML.SEASONALITY."""
    svc = get_bigquery_augmented_analytics_service()
    cycles = [s.strip().upper() for s in seasonalities.split(",")] if seasonalities else ["WEEKLY", "MONTHLY"]

    if dry_run:
        from bigquery_augmented_analytics import BigQueryAugmentedAnalyticsEngine  # type: ignore

        engine = BigQueryAugmentedAnalyticsEngine()
        sql = engine.compile_temporal_profile_sql(table, data_col, timestamp_col, cycles)
        if json_output:
            click.echo(_json.dumps({"dry_run": True, "sql_query": sql}, indent=2))
        else:
            click.echo(f"\n[BigQuery ML.TREND & ML.SEASONALITY TVF Query]\n{sql}\n")
        return

    res = svc.profile_temporal(table, data_col, timestamp_col, cycles)
    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"\n[Stage 1: Temporal Profiling — {res.table}]")
    click.echo(f"  Metric: {res.metric_col} ({res.timestamp_col})")
    click.echo(f"  Trend Slope: {res.trend_slope:+.4f} | Noise Variance: {res.noise_variance:.4f}")
    click.echo("  Seasonal Cycles:")
    for c in res.seasonal_cycles:
        dom = " (dominant)" if c.dominant else ""
        click.echo(f"    - {c.period_name}: strength {c.strength:.2f}{dom}")
    click.echo()


@bigquery_group.command("change-points")
@click.option("--table", required=True, help="Target BigQuery table identifier")
@click.option("--data-col", required=True, help="Metric column name")
@click.option("--timestamp-col", required=True, help="Timestamp column name")
@click.option("--min-prob", default=0.95, type=float, help="Min change point probability (default: 0.95)")
@click.option("--dry-run", is_flag=True, help="Output compiled BigQuery TVF SQL without executing")
@click.option("--json", "json_output", is_flag=True, help="Output JSON result")
def change_points_cli(
    table: str,
    data_col: str,
    timestamp_col: str,
    min_prob: float,
    dry_run: bool,
    json_output: bool,
) -> None:
    """Stage 2: Structural regime shift isolation via ML.DETECT_CHANGE_POINTS."""
    svc = get_bigquery_augmented_analytics_service()

    if dry_run:
        from bigquery_augmented_analytics import BigQueryAugmentedAnalyticsEngine  # type: ignore

        engine = BigQueryAugmentedAnalyticsEngine()
        sql = engine.compile_change_points_sql(table, data_col, timestamp_col, min_prob)
        if json_output:
            click.echo(_json.dumps({"dry_run": True, "sql_query": sql}, indent=2))
        else:
            click.echo(f"\n[BigQuery ML.DETECT_CHANGE_POINTS TVF Query]\n{sql}\n")
        return

    res = svc.detect_change_points(table, data_col, timestamp_col, min_probability=min_prob)
    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"\n[Stage 2: Structural Shift Isolation — {res.table}]")
    click.echo(f"  Primary Shift Timestamp (t0): {res.primary_shift_t0 or 'None'}")
    click.echo(f"  Max Change-Point Probability: {res.max_probability * 100:.1f}%")
    click.echo(f"  Detected Persistent Shifts ({len(res.change_points)} total):")
    for cp in res.change_points:
        click.echo(
            f"    - {cp.start_time} to {cp.end_time}: mean={cp.mean:.1f}, prob={cp.change_point_prob * 100:.1f}%"
        )
    click.echo()


@bigquery_group.command("drivers")
@click.option("--table", required=True, help="Target BigQuery table identifier")
@click.option("--metric-col", required=True, help="Metric column name")
@click.option("--dims", required=True, help="Comma-separated dimension columns")
@click.option("--interest-cond", required=True, help="SQL boolean condition for interest period")
@click.option("--min-support", default=0.01, type=float, help="Min Apriori support (default: 0.01)")
@click.option("--top-k", default=20, type=int, help="Top K drivers (default: 20)")
@click.option("--dry-run", is_flag=True, help="Output compiled BigQuery TVF SQL without executing")
@click.option("--json", "json_output", is_flag=True, help="Output JSON result")
def drivers_cli(
    table: str,
    metric_col: str,
    dims: str,
    interest_cond: str,
    min_support: float,
    top_k: int,
    dry_run: bool,
    json_output: bool,
) -> None:
    """Stage 3: Combinatorial driver attribution via AI.KEY_DRIVERS."""
    svc = get_bigquery_augmented_analytics_service()
    dim_list = [d.strip() for d in dims.split(",") if d.strip()]

    if dry_run:
        from bigquery_augmented_analytics import BigQueryAugmentedAnalyticsEngine  # type: ignore

        engine = BigQueryAugmentedAnalyticsEngine()
        sql = engine.compile_key_drivers_sql(table, metric_col, dim_list, interest_cond, min_support, top_k)
        if json_output:
            click.echo(_json.dumps({"dry_run": True, "sql_query": sql}, indent=2))
        else:
            click.echo(f"\n[BigQuery AI.KEY_DRIVERS Apriori TVF Query]\n{sql}\n")
        return

    res = svc.attribute_drivers(
        table=table,
        metric_col=metric_col,
        dimension_cols=dim_list,
        interest_condition=interest_cond,
        min_apriori_support=min_support,
        top_k=top_k,
    )
    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"\n[Stage 3: Combinatorial Key Drivers — {res.table}]")
    click.echo(f"  Metric: {res.metric_col} | Dimensions: {', '.join(res.dimension_cols)}")
    click.echo(f"  Apriori Support Bound: {res.min_apriori_support} | Top Drivers ({len(res.drivers)}):")
    for d in res.drivers:
        click.echo(
            f"    - [{d.segment}] delta: {d.metric_delta:+.0f}, lift: {d.percentage_change:+.1f}%, contrib: {d.segment_contribution * 100:.1f}%"
        )
    click.echo()


@bigquery_group.command("causal")
@click.option("--table", required=True, help="Target BigQuery table identifier")
@click.option("--data-col", required=True, help="Data column name")
@click.option("--timestamp-col", required=True, help="Timestamp column name")
@click.option("--intervention", required=True, help="Intervention timestamp (e.g. 2026-02-15)")
@click.option("--output-ts/--no-output-ts", default=True, help="Output time-series confidence intervals")
@click.option("--dry-run", is_flag=True, help="Output compiled BigQuery TVF SQL without executing")
@click.option("--json", "json_output", is_flag=True, help="Output JSON result")
def causal_cli(
    table: str,
    data_col: str,
    timestamp_col: str,
    intervention: str,
    output_ts: bool,
    dry_run: bool,
    json_output: bool,
) -> None:
    """Stage 4: Counterfactual causal lift estimation via AI.CAUSAL_EFFECT."""
    svc = get_bigquery_augmented_analytics_service()

    if dry_run:
        from bigquery_augmented_analytics import BigQueryAugmentedAnalyticsEngine  # type: ignore

        engine = BigQueryAugmentedAnalyticsEngine()
        sql = engine.compile_causal_effect_sql(table, data_col, timestamp_col, intervention, output_ts)
        if json_output:
            click.echo(_json.dumps({"dry_run": True, "sql_query": sql}, indent=2))
        else:
            click.echo(f"\n[BigQuery AI.CAUSAL_EFFECT ARIMA_PLUS TVF Query]\n{sql}\n")
        return

    res = svc.estimate_causal_lift(
        table=table,
        data_col=data_col,
        timestamp_col=timestamp_col,
        intervention_timestamp=intervention,
        output_time_series=output_ts,
    )
    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"\n[Stage 4: Counterfactual Causal Lift — {res.table}]")
    click.echo(f"  Intervention Timestamp: {res.intervention_timestamp}")
    click.echo(f"  Actual Volume: {res.actual:,.0f} vs Counterfactual Baseline: {res.counterfactual_baseline:,.0f}")
    click.echo(
        f"  Absolute Lift: {res.absolute_effect:+,.0f} | Relative Lift: {res.relative_effect:+.2f}% (p={res.prob_causal_effect * 100:.1f}%)"
    )
    click.echo()


@bigquery_group.command("pipeline")
@click.option("--table", required=True, help="Target BigQuery table identifier")
@click.option("--metric-col", required=True, help="Metric column name")
@click.option("--timestamp-col", required=True, help="Timestamp column name")
@click.option("--dims", required=True, help="Comma-separated dimension columns")
@click.option("--intervention", help="Optional intervention timestamp (isolated automatically if omitted)")
@click.option("--min-support", default=0.01, type=float, help="Min Apriori support (default: 0.01)")
@click.option("--top-k", default=20, type=int, help="Top K drivers (default: 20)")
@click.option("--dry-run", is_flag=True, help="Execute dry-run investigation with synthetic simulation")
@click.option("--brief", help="Optional path to output HTML visual brief")
@click.option("--json", "json_output", is_flag=True, help="Output JSON result")
def pipeline_cli(
    table: str,
    metric_col: str,
    timestamp_col: str,
    dims: str,
    intervention: str | None,
    min_support: float,
    top_k: int,
    dry_run: bool,
    brief: str | None,
    json_output: bool,
) -> None:
    """Execute complete 5-Stage BigQuery Augmented Analytics pipeline end-to-end."""
    svc = get_bigquery_augmented_analytics_service()
    dim_list = [d.strip() for d in dims.split(",") if d.strip()]

    res = svc.run_investigation(
        target_table=table,
        metric_col=metric_col,
        timestamp_col=timestamp_col,
        dimension_cols=dim_list,
        intervention_timestamp=intervention,
        min_apriori_support=min_support,
        top_k=top_k,
        mock_data={} if dry_run else None,
    )

    if brief:
        brief_path = svc.visual_brief(res, output_path=brief)
        click.echo(f"Visual Brief written to: {brief_path}")

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"\n[BigQuery Augmented Investigation: {res.target_table}]")
    click.echo(f"  When:           {res.narrative.when}")
    click.echo(f"  What:           {res.narrative.what}")
    click.echo(f"  Who:            {res.narrative.who}")
    click.echo(f"  Impact:         {res.narrative.impact}")
    click.echo(f"  Recommendation: {res.narrative.recommendation}\n")


@bigquery_group.command("brief")
@click.option("--table", default="sample_dataset.metrics", help="Target BigQuery table identifier")
@click.option("--metric-col", default="total_trips", help="Metric column name")
@click.option("--timestamp-col", default="trip_date", help="Timestamp column name")
@click.option("--dims", default="subscriber_type,bike_type", help="Comma-separated dimension columns")
@click.option("--output", help="Optional output path for HTML visual brief")
@click.option("--open/--no-open", "open_browser", default=False, help="Open HTML brief in web browser")
def brief_cli(
    table: str,
    metric_col: str,
    timestamp_col: str,
    dims: str,
    output: str | None,
    open_browser: bool,
) -> None:
    """Generate and view interactive HTML visual brief with Mermaid DAG."""
    svc = get_bigquery_augmented_analytics_service()
    dim_list = [d.strip() for d in dims.split(",") if d.strip()]

    report = svc.run_investigation(
        target_table=table,
        metric_col=metric_col,
        timestamp_col=timestamp_col,
        dimension_cols=dim_list,
        mock_data={},
    )
    brief_path = svc.visual_brief(report, output_path=output)
    click.echo(f"\n[Visual Brief Generated]")
    click.echo(f"  Path: {brief_path}\n")

    if open_browser:
        webbrowser.open(brief_path.as_uri())


__all__ = [
    "bigquery_group",
    "get_bigquery_augmented_analytics_service",
]
