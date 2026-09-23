"""Garf Reporting Pipeline Plugin for Brain Harness.

Bridges Google Garf declarative SQL reporting, synthetic simulation,
multi-destination report egress, and two-stage analytical workflow DAGs
into the Brain Harness IoC container.
"""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.garf_reporting import (
    GARF_REPORTING_SERVICE_KEY,
    DefaultGarfReportingService,
    GarfExecutionReceipt,
    GarfQuerySpec,
    GarfReportBatch,
    GarfReportingService,
    GarfWorkflowStep,
)

logger = structlog.get_logger(__name__)


class GarfReportingPlugin(HarnessPlugin, GarfReportingService):
    """Harness Plugin implementing Google Garf declarative SQL reporting."""

    name = "plugin.garf_reporting_pipeline"
    version = "1.0.0"
    description = (
        "Google Garf declarative SQL reporting, simulation, and workflow DAG bridge"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._engine = DefaultGarfReportingService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GARF_REPORTING_SERVICE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(GARF_REPORTING_SERVICE_KEY, self, provider=self.name)
        logger.info("GarfReportingPlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("GarfReportingPlugin unloaded")

    def parse_query(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> GarfQuerySpec:
        """Parse a reporting API SQL query into structured components."""
        return self._engine.parse_query(query_text=query_text, macros=macros)

    def simulate_report(
        self, query_spec: GarfQuerySpec, row_count: int = 5, seed: int = 42
    ) -> GarfReportBatch:
        """Deterministically simulate a tabular report matching query column specs."""
        return self._engine.simulate_report(
            query_spec=query_spec, row_count=row_count, seed=seed
        )

    def write_report(
        self, report: GarfReportBatch, destination_type: str, destination_path: str
    ) -> GarfExecutionReceipt:
        """Write tabular report batch to target storage (CSV, JSON, SQLite)."""
        return self._engine.write_report(
            report=report,
            destination_type=destination_type,
            destination_path=destination_path,
        )

    def execute_query(
        self,
        query_text: str,
        destination_type: str | None = None,
        destination_path: str | None = None,
        macros: dict[str, Any] | None = None,
    ) -> GarfReportBatch:
        """End-to-end execute query: parse, simulate/fetch, and optionally write."""
        return self._engine.execute_query(
            query_text=query_text,
            destination_type=destination_type,
            destination_path=destination_path,
            macros=macros,
        )

    def run_workflow(
        self,
        steps: list[GarfWorkflowStep],
        context_params: dict[str, Any] | None = None,
    ) -> GarfExecutionReceipt:
        """Execute a multi-step analytical workflow DAG."""
        return self._engine.run_workflow(steps=steps, context_params=context_params)


# Module-level tool wrappers for direct tool dispatch
def garf_parse_query(
    query_text: str, macros: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Parse a reporting API SQL query into structured components."""
    spec = plugin.parse_query(query_text=query_text, macros=macros)
    return {
        "status": "ok",
        "title": spec.title,
        "resource_name": spec.resource_name,
        "fields": list(spec.fields),
        "filters": list(spec.filters),
        "sorts": list(spec.sorts),
        "limit": spec.limit,
        "column_names": list(spec.column_names),
        "dynamic_macros": dict(spec.dynamic_macros),
        "virtual_columns": [
            {
                "name": vc.name,
                "expression": vc.expression,
                "source_fields": list(vc.source_fields),
            }
            for vc in spec.virtual_columns
        ],
    }


def garf_simulate_report(
    query_text: str, row_count: int = 5, seed: int = 42
) -> dict[str, Any]:
    """Deterministically simulate a tabular report matching SQL query specifications."""
    spec = plugin.parse_query(query_text=query_text)
    batch = plugin.simulate_report(query_spec=spec, row_count=row_count, seed=seed)
    return {
        "status": "ok",
        "query_title": batch.query_title,
        "column_names": list(batch.column_names),
        "row_count": batch.row_count,
        "rows": [list(r) for r in batch.rows],
        "records": batch.to_dict_list(),
    }


def garf_write_report(
    report_data: dict[str, Any], destination_type: str, destination_path: str
) -> dict[str, Any]:
    """Write a tabular report batch to target storage."""
    batch = GarfReportBatch(
        column_names=tuple(report_data.get("column_names") or []),
        rows=tuple(tuple(r) for r in report_data.get("rows") or []),
        row_count=int(report_data.get("row_count", 0)),
        query_title=report_data.get("query_title"),
    )
    receipt = plugin.write_report(
        report=batch,
        destination_type=destination_type,
        destination_path=destination_path,
    )
    return {
        "status": receipt.status,
        "operation": receipt.operation,
        "row_count": receipt.row_count,
        "elapsed_seconds": receipt.elapsed_seconds,
        "details": dict(receipt.details),
    }


def garf_execute_query(
    query_text: str,
    destination_type: str | None = None,
    destination_path: str | None = None,
    macros: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """End-to-end execution: parses query, simulates/fetches report, and optionally writes output."""
    batch = plugin.execute_query(
        query_text=query_text,
        destination_type=destination_type,
        destination_path=destination_path,
        macros=macros,
    )
    return {
        "status": "ok",
        "query_title": batch.query_title,
        "column_names": list(batch.column_names),
        "row_count": batch.row_count,
        "records": batch.to_dict_list(),
    }


def garf_run_workflow(
    steps: list[dict[str, Any]],
    context_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a multi-step analytical workflow DAG."""
    workflow_steps = [
        GarfWorkflowStep(
            step_id=str(s["step_id"]),
            step_type=str(s["step_type"]),
            query_path=s.get("query_path"),
            writer_type=s.get("writer_type"),
            destination=s.get("destination"),
            depends_on=tuple(s.get("depends_on") or ()),
            sql_query=s.get("sql_query"),
        )
        for s in steps
    ]
    receipt = plugin.run_workflow(steps=workflow_steps, context_params=context_params)
    return {
        "status": receipt.status,
        "operation": receipt.operation,
        "row_count": receipt.row_count,
        "elapsed_seconds": receipt.elapsed_seconds,
        "details": dict(receipt.details),
    }


# Export authoritative module-level singleton (Rule 45)
plugin = GarfReportingPlugin()
