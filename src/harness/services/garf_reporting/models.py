"""Slotted domain models, protocols, and service keys for Garf reporting (Rule 12)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@dataclass(slots=True, frozen=True)
class VirtualColumnSpec:
    """Immutable specification for a calculated or transformed virtual column."""

    name: str
    expression: str
    source_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Virtual column name cannot be empty")
        if not self.expression:
            raise ValueError("Virtual column expression cannot be empty")


@dataclass(slots=True, frozen=True)
class GarfQuerySpec:
    """Immutable parsed query specification and metadata."""

    text: str
    title: str | None = None
    resource_name: str | None = None
    fields: tuple[str, ...] = ()
    filters: tuple[str, ...] = ()
    sorts: tuple[str, ...] = ()
    limit: int | None = None
    column_names: tuple[str, ...] = ()
    dynamic_macros: tuple[tuple[str, str], ...] = ()
    virtual_columns: tuple[VirtualColumnSpec, ...] = ()

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("Query text cannot be empty")


@dataclass(slots=True, frozen=True)
class GarfReportBatch:
    """Immutable normalized tabular report batch."""

    column_names: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    row_count: int
    query_title: str | None = None

    def __post_init__(self) -> None:
        if self.row_count != len(self.rows):
            raise ValueError(
                f"Row count mismatch: declared {self.row_count}, actual {len(self.rows)}"
            )

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert rows to list of column-keyed dictionaries."""
        return [dict(zip(self.column_names, row)) for row in self.rows]


@dataclass(slots=True, frozen=True)
class GarfWorkflowStep:
    """Immutable workflow step definition within an execution DAG."""

    step_id: str
    step_type: str  # 'query', 'sql', 'writer'
    query_path: str | None = None
    writer_type: str | None = None
    destination: str | None = None
    depends_on: tuple[str, ...] = ()
    sql_query: str | None = None

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("step_id cannot be empty")
        if self.step_type not in ("query", "sql", "writer"):
            raise ValueError(f"Invalid step_type: {self.step_type}")


@dataclass(slots=True, frozen=True)
class GarfExecutionReceipt:
    """Immutable receipt summarizing a reporting or workflow execution."""

    status: str
    operation: str
    row_count: int
    elapsed_seconds: float
    details: tuple[tuple[str, str], ...] = ()

    def get_detail(self, key: str) -> str | None:
        """Retrieve single detail value by key."""
        for k, v in self.details:
            if k == key:
                return v
        return None


@runtime_checkable
class GarfReportingService(Protocol):
    """Protocol for Garf declarative SQL reporting and data pipelines."""

    def parse_query(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> GarfQuerySpec:
        """Parse a reporting API SQL query into structured components."""
        ...

    def simulate_report(
        self, query_spec: GarfQuerySpec, row_count: int = 5, seed: int = 42
    ) -> GarfReportBatch:
        """Deterministically simulate a tabular report matching query column specs."""
        ...

    def write_report(
        self, report: GarfReportBatch, destination_type: str, destination_path: str
    ) -> GarfExecutionReceipt:
        """Write tabular report batch to target storage (CSV, JSON, SQLite)."""
        ...

    def execute_query(
        self,
        query_text: str,
        destination_type: str | None = None,
        destination_path: str | None = None,
        macros: dict[str, Any] | None = None,
    ) -> GarfReportBatch:
        """End-to-end execute query: parse, simulate/fetch, and optionally write."""
        ...

    def run_workflow(
        self,
        steps: list[GarfWorkflowStep],
        context_params: dict[str, Any] | None = None,
    ) -> GarfExecutionReceipt:
        """Execute a multi-step analytical workflow DAG."""
        ...


GARF_REPORTING_SERVICE_KEY: ServiceKey[GarfReportingService] = ServiceKey(
    "garf_reporting_service"
)
