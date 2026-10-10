"""Core DefaultGarfReportingService coordinator implementation."""

from __future__ import annotations

from typing import Any

import structlog

from .exporters import write_report
from .models import (
    GarfExecutionReceipt,
    GarfQuerySpec,
    GarfReportBatch,
    GarfWorkflowStep,
)
from .parser import expand_macros, parse_query
from .simulator import simulate_report
from .workflow import run_workflow_dag

logger = structlog.get_logger(__name__)


class DefaultGarfReportingService:
    """Production implementation of GarfReportingService."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger(__name__)

    def _expand_macros(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> tuple[str, tuple[tuple[str, str], ...]]:
        """Expand dynamic date macros and user-provided macro variables."""
        return expand_macros(query_text, macros)

    def parse_query(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> GarfQuerySpec:
        """Parse a reporting API SQL query into structured components."""
        return parse_query(query_text, macros)

    def simulate_report(
        self, query_spec: GarfQuerySpec, row_count: int = 5, seed: int = 42
    ) -> GarfReportBatch:
        """Deterministically simulate a tabular report matching query column specs."""
        return simulate_report(query_spec, row_count=row_count, seed=seed)

    def write_report(
        self, report: GarfReportBatch, destination_type: str, destination_path: str
    ) -> GarfExecutionReceipt:
        """Write tabular report batch to target storage (CSV, JSON, SQLite)."""
        return write_report(report, destination_type, destination_path)

    def execute_query(
        self,
        query_text: str,
        destination_type: str | None = None,
        destination_path: str | None = None,
        macros: dict[str, Any] | None = None,
    ) -> GarfReportBatch:
        """End-to-end execute query: parse, simulate/fetch, and optionally write."""
        spec = self.parse_query(query_text, macros)
        report = self.simulate_report(spec)
        if destination_type and destination_path:
            self.write_report(report, destination_type, destination_path)
        return report

    def run_workflow(
        self,
        steps: list[GarfWorkflowStep],
        context_params: dict[str, Any] | None = None,
    ) -> GarfExecutionReceipt:
        """Execute a multi-step analytical workflow DAG."""
        return run_workflow_dag(self, steps, context_params)
