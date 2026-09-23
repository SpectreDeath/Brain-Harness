"""Tests for GarfReportingService, domain models, and GarfReportingPlugin."""

import tempfile
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.garf_reporting import (
    GARF_REPORTING_SERVICE_KEY,
    DefaultGarfReportingService,
    GarfExecutionReceipt,
    GarfQuerySpec,
    GarfReportBatch,
    GarfWorkflowStep,
)
from plugins.data_engineering.garf_reporting_pipeline.main import (
    GarfReportingPlugin,
    plugin,
)


@pytest.mark.unit
def test_garf_slotted_frozen_immutability() -> None:
    """Verify slotted and frozen dataclass architecture invariant (Rule 12, Rule 43)."""
    spec = GarfQuerySpec(
        text="SELECT id FROM campaign",
        title="test_query",
        resource_name="campaign",
        column_names=("id",),
    )
    # Rule 43: Direct attribute assignment inside pytest.raises
    with pytest.raises((AttributeError, TypeError)):
        spec.title = "modified_title"  # type: ignore

    batch = GarfReportBatch(
        column_names=("id", "clicks"),
        rows=((1, 100), (2, 200)),
        row_count=2,
        query_title="batch_test",
    )
    with pytest.raises((AttributeError, TypeError)):
        batch.row_count = 5  # type: ignore

    step = GarfWorkflowStep(step_id="s1", step_type="query", sql_query="SELECT 1")
    with pytest.raises((AttributeError, TypeError)):
        step.step_id = "s2"  # type: ignore

    receipt = GarfExecutionReceipt(
        status="ok", operation="write", row_count=10, elapsed_seconds=0.01
    )
    with pytest.raises((AttributeError, TypeError)):
        receipt.status = "error"  # type: ignore


@pytest.mark.unit
def test_garf_query_parser_and_macros() -> None:
    """Verify declarative SQL parsing and dynamic macro resolution."""
    service = DefaultGarfReportingService()
    query = (
        "/* title: campaign_clicks */ "
        "SELECT campaign.id AS id, metrics.clicks AS clicks, segments.date AS date "
        "FROM campaign "
        "WHERE segments.date = :TODAY AND campaign.status = 'ACTIVE' "
        "ORDER BY metrics.clicks DESC "
        "LIMIT 10"
    )

    spec = service.parse_query(query)
    assert spec.title == "campaign_clicks"
    assert spec.resource_name == "campaign"
    assert spec.column_names == ("id", "clicks", "date")
    assert spec.limit == 10
    assert len(spec.filters) >= 2
    assert any(":TODAY" in m[0] for m in spec.dynamic_macros)


@pytest.mark.unit
def test_garf_simulate_report_deterministic() -> None:
    """Verify deterministic zero-network report simulation."""
    service = DefaultGarfReportingService()
    spec = service.parse_query(
        "SELECT id, name, metrics.clicks AS clicks, metrics.cost AS cost FROM ad_group LIMIT 5"
    )

    batch1 = service.simulate_report(spec, row_count=5, seed=42)
    batch2 = service.simulate_report(spec, row_count=5, seed=42)

    assert batch1.row_count == 5
    assert batch1.column_names == ("id", "name", "clicks", "cost")
    assert batch1.rows == batch2.rows

    dicts = batch1.to_dict_list()
    assert len(dicts) == 5
    assert isinstance(dicts[0]["id"], int)
    assert isinstance(dicts[0]["clicks"], int)
    assert isinstance(dicts[0]["cost"], float)


@pytest.mark.unit
def test_garf_egress_writers() -> None:
    """Verify report writers for CSV, JSON, and SQLite."""
    service = DefaultGarfReportingService()
    spec = service.parse_query("SELECT id, name, clicks FROM campaign LIMIT 3")
    batch = service.simulate_report(spec, row_count=3)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # CSV Writer
        csv_file = tmp_path / "report.csv"
        receipt_csv = service.write_report(batch, "csv", str(csv_file))
        assert receipt_csv.status == "ok"
        assert csv_file.exists()
        assert csv_file.stat().st_size > 0

        # JSON Writer
        json_file = tmp_path / "report.json"
        receipt_json = service.write_report(batch, "json", str(json_file))
        assert receipt_json.status == "ok"
        assert json_file.exists()
        assert json_file.stat().st_size > 0

        # SQLite Writer
        sqlite_file = tmp_path / "report.db"
        receipt_sqlite = service.write_report(batch, "sqlite", str(sqlite_file))
        assert receipt_sqlite.status == "ok"
        assert sqlite_file.exists()


@pytest.mark.unit
def test_garf_workflow_dag_execution() -> None:
    """Verify two-stage analytical workflow DAG with post-processing SQL."""
    service = DefaultGarfReportingService()

    with tempfile.TemporaryDirectory() as tmpdir:
        sqlite_db = str(Path(tmpdir) / "analytics.db")

        steps = [
            GarfWorkflowStep(
                step_id="extract_campaigns",
                step_type="query",
                sql_query="SELECT id, name, metrics.clicks AS clicks FROM campaign LIMIT 5",
                writer_type="sqlite",
                destination=sqlite_db,
            ),
            GarfWorkflowStep(
                step_id="post_process_kpi",
                step_type="sql",
                sql_query="CREATE TABLE campaign_kpi AS SELECT count(*) as total_count FROM campaign",
                destination=sqlite_db,
                depends_on=("extract_campaigns",),
            ),
        ]

        receipt = service.run_workflow(steps)
        assert receipt.status == "ok"
        assert receipt.get_detail("step_count") == "2"
        assert "extract_campaigns,post_process_kpi" == receipt.get_detail(
            "executed_steps"
        )


@pytest.mark.unit
def test_garf_plugin_ioc_registration() -> None:
    """Verify GarfReportingPlugin IoC registration into ServiceContext (Rule 1, Rule 2)."""
    context = ServiceContext()
    garf_plugin = GarfReportingPlugin()

    # Verify service key declared in provides
    assert GARF_REPORTING_SERVICE_KEY in garf_plugin.provides

    # On load provides service
    garf_plugin.on_load(context)
    resolved = context.require(GARF_REPORTING_SERVICE_KEY)
    assert resolved is garf_plugin

    # Verify authoritative module-level singleton (Rule 45)
    assert isinstance(plugin, GarfReportingPlugin)


@pytest.mark.unit
def test_garf_virtual_columns() -> None:
    """Verify virtual column expression extraction, typing, and simulation."""
    service = DefaultGarfReportingService()
    query = (
        "SELECT campaign.id AS id, "
        "metrics.cost_micros / 1000000 AS cost, "
        "'SEARCH' AS network "
        "FROM campaign LIMIT 3"
    )
    spec = service.parse_query(query)
    assert spec.column_names == ("id", "cost", "network")
    assert len(spec.virtual_columns) == 2

    vc_names = {vc.name: vc for vc in spec.virtual_columns}
    assert "cost" in vc_names
    assert vc_names["cost"].expression == "metrics.cost_micros / 1000000"
    assert "metrics.cost_micros" in vc_names["cost"].source_fields

    assert "network" in vc_names
    assert vc_names["network"].expression == "'SEARCH'"

    # Verify simulation evaluates virtual columns
    batch = service.simulate_report(spec, row_count=3)
    assert batch.row_count == 3
    dicts = batch.to_dict_list()
    assert dicts[0]["network"] == "SEARCH"
    assert isinstance(dicts[0]["cost"], float)
    assert isinstance(dicts[0]["id"], int)


@pytest.mark.unit
def test_garf_sqlite_column_type_inference() -> None:
    """Verify SQLite column datatype affinity inference (INTEGER, REAL, TEXT)."""
    import sqlite3

    service = DefaultGarfReportingService()
    spec = service.parse_query(
        "SELECT campaign.id AS id, campaign.name AS name, metrics.clicks AS clicks, "
        "metrics.cost_micros / 1000000 AS cost FROM campaign LIMIT 3"
    )
    batch = service.simulate_report(spec, row_count=3)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "typed_test.db"
        service.write_report(batch, "sqlite", str(db_path))

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute('PRAGMA table_info("campaign")')
        pragma_cols = {row[1]: row[2] for row in cur.fetchall()}
        conn.close()

        assert pragma_cols.get("id") == "INTEGER"
        assert pragma_cols.get("clicks") == "INTEGER"
        assert pragma_cols.get("cost") == "REAL"
        assert pragma_cols.get("name") == "TEXT"


@pytest.mark.unit
def test_garf_workflow_query_file_and_writer_step() -> None:
    """Verify DAG file loading (query_path), SQL macro expansion, and writer step execution."""
    service = DefaultGarfReportingService()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        query_file = tmp_p / "extract.sql"
        query_file.write_text(
            "SELECT id, name, metrics.clicks AS clicks FROM campaign WHERE metrics.clicks > :threshold LIMIT 5",
            encoding="utf-8",
        )

        staging_db = str(tmp_p / "staging.db")
        final_json = str(tmp_p / "final.json")

        steps = [
            GarfWorkflowStep(
                step_id="step_extract",
                step_type="query",
                query_path=str(query_file),
                writer_type="sqlite",
                destination=staging_db,
            ),
            GarfWorkflowStep(
                step_id="step_transform",
                step_type="sql",
                sql_query="CREATE TABLE filtered_kpis AS SELECT id, clicks FROM campaign WHERE clicks >= :threshold",
                destination=staging_db,
                depends_on=("step_extract",),
            ),
            GarfWorkflowStep(
                step_id="step_export",
                step_type="writer",
                writer_type="json",
                destination=final_json,
                query_path=staging_db,
                depends_on=("step_transform",),
            ),
        ]

        receipt = service.run_workflow(steps, context_params={"threshold": 100})
        assert receipt.status == "ok"
        assert receipt.get_detail("step_count") == "3"
        assert Path(final_json).exists()
        assert Path(final_json).stat().st_size > 0
