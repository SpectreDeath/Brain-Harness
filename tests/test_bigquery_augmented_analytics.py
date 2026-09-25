"""Test suite for BigQuery Augmented Analytics domain engine, IoC service, plugin, and CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

_SKILL_SCRIPTS = (
    Path(__file__).parent.parent
    / ".agents"
    / "skills"
    / "bigquery-augmented-analytics"
    / "scripts"
)
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from bigquery_augmented_analytics import (
    AugmentedInvestigationResult,
    BigQueryAugmentedAnalyticsEngine,
    ChangePointItem,
    DriverSegmentItem,
    ExecutiveDiagnosticNarrative,
    SeasonalityCycle,
    TemporalTrendPoint,
)

from harness.cli import main as cli_main
from harness.creator.skills import SkillValidator
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.bigquery_augmented_analytics import (
    BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY,
    AugmentedInvestigationData,
    BigQueryAugmentedAnalyticsService,
)
from plugins.data_engineering.bigquery_augmented_analytics.main import (
    BigQueryAugmentedAnalyticsPlugin,
    bigquery_attribute_drivers,
    bigquery_augmented_pipeline,
    bigquery_causal_lift,
    bigquery_detect_change_points,
    bigquery_temporal_profile,
    bigquery_visual_brief,
)
from plugins.data_engineering.bigquery_augmented_analytics.main import (
    plugin as bq_plugin_singleton,
)

# ---------------------------------------------------------------------------
# 1. Slotted & Frozen Dataclass Immutability Tests (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


def test_frozen_dataclass_immutability() -> None:
    """Verify slotted & frozen dataclasses raise AttributeError/TypeError on attribute mutation."""
    trend_pt = TemporalTrendPoint(date="2026-01-01", value=100.0, trend=98.5, noise=1.5)
    with pytest.raises((AttributeError, TypeError)):
        trend_pt.value = 110.0  # type: ignore

    cycle = SeasonalityCycle(period_name="WEEKLY", strength=0.85, dominant=True)
    with pytest.raises((AttributeError, TypeError)):
        cycle.dominant = False  # type: ignore

    cp_item = ChangePointItem(
        start_time="2026-02-01",
        end_time="2026-02-28",
        mean=150.0,
        variance=12.0,
        change_point_prob=0.98,
    )
    with pytest.raises((AttributeError, TypeError)):
        cp_item.change_point_prob = 0.5  # type: ignore

    seg_item = DriverSegmentItem(
        segment="dim=val",
        metric_delta=500.0,
        percentage_change=15.0,
        segment_contribution=0.45,
        dimension_values={"dim": "val"},
    )
    with pytest.raises((AttributeError, TypeError)):
        seg_item.metric_delta = 0.0  # type: ignore

    narrative = ExecutiveDiagnosticNarrative(
        when="2026-02-01",
        what="Trend slope +0.05",
        who="Segment A",
        impact="Lift +25%",
        recommendation="Maintain policy",
    )
    with pytest.raises((AttributeError, TypeError)):
        narrative.when = "modified"  # type: ignore


# ---------------------------------------------------------------------------
# 2. BigQuery TVF SQL Compiler Tests
# ---------------------------------------------------------------------------


def test_compile_temporal_profile_sql() -> None:
    """Verify ML.TREND and ML.SEASONALITY TVF SQL compilation."""
    engine = BigQueryAugmentedAnalyticsEngine()
    sql = engine.compile_temporal_profile_sql(
        table="project.dataset.events",
        data_col="conversions",
        timestamp_col="event_time",
        seasonalities=["WEEKLY", "MONTHLY"],
    )
    assert "ML.TREND(" in sql
    assert "ML.SEASONALITY(" in sql
    assert "data_col => 'conversions'" in sql
    assert "timestamp_col => 'metric_date'" in sql
    assert "'WEEKLY'" in sql and "'MONTHLY'" in sql


def test_compile_change_points_sql() -> None:
    """Verify ML.DETECT_CHANGE_POINTS TVF SQL compilation and probability filter."""
    engine = BigQueryAugmentedAnalyticsEngine()
    sql = engine.compile_change_points_sql(
        table="project.dataset.events",
        data_col="conversions",
        timestamp_col="event_time",
        min_probability=0.95,
    )
    assert "ML.DETECT_CHANGE_POINTS(" in sql
    assert "change_point_prob >= 0.95" in sql
    assert "ORDER BY start_time DESC" in sql


def test_compile_key_drivers_sql_and_apriori_guardrails() -> None:
    """Verify AI.KEY_DRIVERS Apriori TVF compilation and micro-segment noise guardrails."""
    engine = BigQueryAugmentedAnalyticsEngine()

    # Valid compilation
    sql = engine.compile_key_drivers_sql(
        table="project.dataset.events",
        metric_col="conversions",
        dimension_cols=["country", "device_type"],
        interest_period_condition="DATE(event_time) >= '2026-02-01'",
        min_apriori_support=0.02,
        top_k=15,
    )
    assert "AI.KEY_DRIVERS(" in sql
    assert "dimension_cols => ['country', 'device_type']" in sql
    assert "min_apriori_support => 0.02" in sql
    assert "top_k => 15" in sql

    # Anti-pattern check: support < 0.001 raises ValueError
    with pytest.raises(ValueError, match="min_apriori_support"):
        engine.compile_key_drivers_sql(
            table="project.dataset.events",
            metric_col="conversions",
            dimension_cols=["country"],
            interest_period_condition="TRUE",
            min_apriori_support=0.0001,
        )


def test_compile_causal_effect_sql() -> None:
    """Verify AI.CAUSAL_EFFECT ARIMA_PLUS counterfactual TVF SQL compilation."""
    engine = BigQueryAugmentedAnalyticsEngine()
    sql = engine.compile_causal_effect_sql(
        table="project.dataset.events",
        data_col="conversions",
        timestamp_col="event_time",
        intervention_timestamp="2026-02-15",
        output_time_series=True,
    )
    assert "AI.CAUSAL_EFFECT(" in sql
    assert "TIMESTAMP('2026-02-15')" in sql
    assert "output_time_series => TRUE" in sql
    assert "counterfactual_baseline" in sql
    assert "lower_bound" in sql and "upper_bound" in sql


# ---------------------------------------------------------------------------
# 3. Analytical Pipeline & Executive Narrative Tests
# ---------------------------------------------------------------------------


def test_investigative_pipeline_end_to_end(tmp_path: Path) -> None:
    """Verify end-to-end 5-stage investigative pipeline and visual brief generation."""
    engine = BigQueryAugmentedAnalyticsEngine()
    result = engine.run_investigative_pipeline(
        target_table="austin_bikeshare.trips",
        metric_col="trip_id",
        timestamp_col="start_time",
        dimension_cols=["subscriber_type", "bike_type"],
        mock_data={},
    )

    assert isinstance(result, AugmentedInvestigationResult)
    assert result.target_table == "austin_bikeshare.trips"
    assert result.temporal_profile.trend_slope == pytest.approx(0.048, 0.001)
    assert result.change_points.primary_shift_t0 == "2026-02-15 00:00:00"
    assert len(result.key_drivers.drivers) > 0
    assert result.causal_effect.relative_effect > 0
    assert "Persistent structural regime shift" in result.narrative.when
    assert "Double down" in result.narrative.recommendation

    # Verify visual brief generation (Rule 51 compliant)
    brief_out = tmp_path / "test_brief.html"
    generated_path = engine.generate_visual_brief(result, output_path=brief_out)
    assert generated_path.exists()
    content = generated_path.read_text(encoding="utf-8")
    assert "BigQuery Augmented Analytics Visual Brief" in content
    assert "austin_bikeshare.trips" in content
    assert "AI.KEY_DRIVERS" in content
    assert "mermaid" in content


# ---------------------------------------------------------------------------
# 4. Micro-Kernel IoC Service Protocol & Plugin Tests (Rule 49 & Rule 45)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ioc_service_registration_and_resolution() -> None:
    """Verify BigQueryAugmentedAnalyticsService IoC registration and resolution."""
    context = ServiceContext()
    plugin = BigQueryAugmentedAnalyticsPlugin()

    # Verify protocol compliance
    assert isinstance(plugin, BigQueryAugmentedAnalyticsService)

    # Register into IoC container
    await plugin.on_load(context)

    # Resolve from IoC container
    resolved = context.require(BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY)
    assert resolved is plugin

    # Test service methods
    report = resolved.run_investigation(
        target_table="austin_bikeshare.trips",
        metric_col="trip_id",
        timestamp_col="start_time",
        dimension_cols=["subscriber_type", "bike_type"],
        mock_data={},
    )
    assert isinstance(report, AugmentedInvestigationData)
    assert report.target_table == "austin_bikeshare.trips"
    assert report.dry_run is True


def test_plugin_module_singleton_and_top_level_tools() -> None:
    """Verify plugin module singleton export and top-level tool functions."""
    assert bq_plugin_singleton is not None
    assert isinstance(bq_plugin_singleton, BigQueryAugmentedAnalyticsPlugin)
    assert bq_plugin_singleton.name == "plugin.bigquery_augmented_analytics"
    assert BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY in bq_plugin_singleton.provides

    # Test top-level tool functions
    t_prof = bigquery_temporal_profile(
        table="test.tbl", data_col="trips", timestamp_col="date"
    )
    assert "trend_slope" in t_prof

    t_cp = bigquery_detect_change_points(
        table="test.tbl", data_col="trips", timestamp_col="date"
    )
    assert "change_points" in t_cp

    t_dr = bigquery_attribute_drivers(
        table="test.tbl",
        metric_col="trips",
        dimension_cols=["sub", "bike"],
        interest_condition="date >= '2026-01-01'",
    )
    assert "drivers" in t_dr

    t_ca = bigquery_causal_lift(
        table="test.tbl",
        data_col="trips",
        timestamp_col="date",
        intervention_timestamp="2026-02-15",
    )
    assert "absolute_effect" in t_ca

    t_pipe = bigquery_augmented_pipeline(
        table="test.tbl",
        metric_col="trips",
        timestamp_col="date",
        dimension_cols=["sub"],
        dry_run=True,
    )
    assert "narrative" in t_pipe

    brief_html = bigquery_visual_brief(
        table="test.tbl", metric_col="trips", timestamp_col="date"
    )
    assert Path(brief_html).exists()


def test_plugin_and_skill_validator_compliance() -> None:
    """Verify zero-warning compliance with PluginValidator and SkillValidator."""
    p_report = PluginValidator.validate_sync("plugins/data_engineering/bigquery_augmented_analytics")
    assert p_report.valid is True
    assert len(p_report.errors) == 0

    s_report = SkillValidator.validate_sync(".agents/skills/bigquery-augmented-analytics")
    assert s_report.valid is True
    assert len([c for c in s_report.checks if not c.passed]) == 0


# ---------------------------------------------------------------------------
# 5. Headless Click CLI Tests (Rule 10 & Rule 6)
# ---------------------------------------------------------------------------


def test_cli_subcommands() -> None:
    """Verify headless Click CLI subcommands via CliRunner."""
    runner = CliRunner()

    # Top-level help
    res_help = runner.invoke(cli_main, ["bq", "--help"])
    assert res_help.exit_code == 0
    assert "profile" in res_help.output
    assert "change-points" in res_help.output
    assert "drivers" in res_help.output
    assert "causal" in res_help.output
    assert "pipeline" in res_help.output

    # bq profile dry-run
    res_prof = runner.invoke(
        cli_main,
        ["bq", "profile", "--table", "tbl", "--data-col", "val", "--timestamp-col", "dt", "--dry-run"],
    )
    assert res_prof.exit_code == 0
    assert "ML.TREND" in res_prof.output

    # bq change-points dry-run
    res_cp = runner.invoke(
        cli_main,
        ["bq", "change-points", "--table", "tbl", "--data-col", "val", "--timestamp-col", "dt", "--dry-run"],
    )
    assert res_cp.exit_code == 0
    assert "ML.DETECT_CHANGE_POINTS" in res_cp.output

    # bq drivers dry-run
    res_dr = runner.invoke(
        cli_main,
        [
            "bq",
            "drivers",
            "--table",
            "tbl",
            "--metric-col",
            "val",
            "--dims",
            "dim_a,dim_b",
            "--interest-cond",
            "dt >= '2026-01-01'",
            "--dry-run",
        ],
    )
    assert res_dr.exit_code == 0
    assert "AI.KEY_DRIVERS" in res_dr.output

    # bq causal dry-run
    res_ca = runner.invoke(
        cli_main,
        ["bq", "causal", "--table", "tbl", "--data-col", "val", "--timestamp-col", "dt", "--intervention", "2026-02-15", "--dry-run"],
    )
    assert res_ca.exit_code == 0
    assert "AI.CAUSAL_EFFECT" in res_ca.output

    # bq pipeline dry-run
    res_pipe = runner.invoke(
        cli_main,
        [
            "bq",
            "pipeline",
            "--table",
            "austin.trips",
            "--metric-col",
            "trip_id",
            "--timestamp-col",
            "start_time",
            "--dims",
            "subscriber_type,bike_type",
            "--dry-run",
        ],
    )
    assert res_pipe.exit_code == 0
    assert "[BigQuery Augmented Investigation: austin.trips]" in res_pipe.output
    assert "When:" in res_pipe.output
    assert "Recommendation:" in res_pipe.output
