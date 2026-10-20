"""Contract and invariant verification for Garf Reporting decomposition per AGENTS.md Rules 11, 12, 43, and 58."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.garf_reporting import (
    GARF_REPORTING_SERVICE_KEY,
    DefaultGarfReportingService,
    GarfExecutionReceipt,
    GarfQuerySpec,
    GarfReportBatch,
    GarfReportingService,
    GarfWorkflowStep,
    VirtualColumnSpec,
    expand_macros,
    parse_query,
    resolve_garf_reporting,
    run_workflow_dag,
    simulate_report,
    write_report,
)


def test_garf_reporting_subpackage_line_bounds() -> None:
    """Enforce Rule 11: All files in src/harness/services/garf_reporting must be strictly < 200 lines."""
    pkg_dir = Path(__file__).resolve().parent.parent / "src" / "harness" / "services" / "garf_reporting"
    assert pkg_dir.is_dir()

    for p in pkg_dir.glob("*.py"):
        line_count = len(p.read_text(encoding="utf-8").splitlines())
        assert (
            line_count < 200
        ), f"File {p.name} has {line_count} lines, exceeding 200 line limit!"


def test_garf_reporting_subpackage_exports() -> None:
    """Verify all public symbols are exported cleanly from the subpackage facade."""
    assert issubclass(VirtualColumnSpec, object)
    assert issubclass(GarfQuerySpec, object)
    assert issubclass(GarfReportBatch, object)
    assert issubclass(GarfWorkflowStep, object)
    assert issubclass(GarfExecutionReceipt, object)
    assert issubclass(DefaultGarfReportingService, object)
    assert GARF_REPORTING_SERVICE_KEY.name == "garf_reporting_service"
    assert callable(resolve_garf_reporting)
    assert callable(expand_macros)
    assert callable(parse_query)
    assert callable(simulate_report)
    assert callable(write_report)
    assert callable(run_workflow_dag)


def test_garf_slotted_frozen_dataclass_immutability() -> None:
    """Enforce Rule 12 & Rule 43: Domain models must be slotted and frozen."""
    vc = VirtualColumnSpec(name="cost", expression="micros / 1000000")
    assert vc.name == "cost"
    assert hasattr(vc, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        vc.name = "changed"  # type: ignore[misc]

    query = GarfQuerySpec(text="SELECT id FROM resource")
    assert query.text == "SELECT id FROM resource"
    assert hasattr(query, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        query.text = "changed"  # type: ignore[misc]

    batch = GarfReportBatch(column_names=("c1",), rows=((1,),), row_count=1)
    assert batch.row_count == 1
    assert hasattr(batch, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        batch.row_count = 99  # type: ignore[misc]


def test_single_seam_resolver_contract() -> None:
    """Enforce Rule 58: resolve_garf_reporting across targets."""
    # 1. Target is None -> new default instance
    svc1 = resolve_garf_reporting()
    assert isinstance(svc1, GarfReportingService)

    # 2. Target is existing service -> returns identity
    assert resolve_garf_reporting(svc1) is svc1

    # 3. Target is ServiceContext -> resolves or registers onto GARF_REPORTING_SERVICE_KEY
    context = ServiceContext()
    assert context.optional(GARF_REPORTING_SERVICE_KEY) is None
    svc2 = resolve_garf_reporting(context)
    assert isinstance(svc2, GarfReportingService)
    assert context.optional(GARF_REPORTING_SERVICE_KEY) is svc2

    # Idempotent re-resolution
    svc3 = resolve_garf_reporting(context)
    assert svc3 is svc2


def test_parser_and_macros_in_isolation() -> None:
    """Verify query parser and macro expansion in isolation."""
    query = "SELECT campaign.id, metrics.clicks, metrics.cost_micros / 1000000 AS cost FROM campaign WHERE segments.date = :TODAY"
    spec = parse_query(query)
    assert spec.resource_name == "campaign"
    assert "cost" in spec.column_names
    assert len(spec.virtual_columns) == 1
    assert spec.virtual_columns[0].name == "cost"


def test_simulator_and_egress_in_isolation(tmp_path: Path) -> None:
    """Verify deterministic simulation and multi-destination egress in isolation."""
    query = "SELECT campaign.id, metrics.clicks FROM campaign"
    spec = parse_query(query)
    report = simulate_report(spec, row_count=3, seed=42)
    assert report.row_count == 3
    assert len(report.rows) == 3

    # CSV egress
    csv_file = tmp_path / "report.csv"
    receipt_csv = write_report(report, "csv", str(csv_file))
    assert receipt_csv.status == "ok"
    assert csv_file.exists()

    # JSON egress
    json_file = tmp_path / "report.json"
    receipt_json = write_report(report, "json", str(json_file))
    assert receipt_json.status == "ok"
    assert json_file.exists()


def test_workflow_dag_in_isolation(tmp_path: Path) -> None:
    """Verify workflow step DAG execution."""
    service = DefaultGarfReportingService()
    db_path = tmp_path / "staging.db"
    steps = [
        GarfWorkflowStep(
            step_id="step1",
            step_type="query",
            sql_query="SELECT campaign.id, metrics.clicks FROM campaign",
            writer_type="sqlite",
            destination=str(db_path),
        ),
    ]
    receipt = run_workflow_dag(service, steps)
    assert receipt.status == "ok"
    assert db_path.exists()
