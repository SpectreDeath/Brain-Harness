"""Google Garf Declarative SQL Reporting Service & Domain Models.

Provides query parsing for reporting APIs, macro and virtual column resolution,
deterministic zero-network simulation, multi-destination report egress,
and two-stage analytical workflow DAG orchestration.
"""

from __future__ import annotations

import csv
import datetime
import json
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Slotted & Frozen Domain Models (Rule 12)
# ---------------------------------------------------------------------------


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
        for k, v in self.details:
            if k == key:
                return v
        return None


# ---------------------------------------------------------------------------
# Service Protocol & ServiceKey (Rule 2, Rule 49)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class DefaultGarfReportingService:
    """Production implementation of GarfReportingService."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger(__name__)

    def _expand_macros(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> tuple[str, tuple[tuple[str, str], ...]]:
        """Expand dynamic date macros and user-provided macro variables."""
        expanded = query_text
        macro_records: list[tuple[str, str]] = []
        today = datetime.datetime.now(datetime.timezone.utc).date()

        # Dynamic date macro pattern: :YYYYMMDD-N or :YYYYMMDD+N
        date_pattern = re.compile(r":YYYYMMDD([+-]\d+)?")

        def _replace_date(match: re.Match[str]) -> str:
            delta_str = match.group(1)
            target_date = today
            if delta_str:
                days = int(delta_str)
                target_date = today + datetime.timedelta(days=days)
            res = target_date.strftime("%Y-%m-%d")
            macro_records.append((match.group(0), res))
            return f"'{res}'"

        expanded = date_pattern.sub(_replace_date, expanded)

        # :TODAY macro
        if ":TODAY" in expanded:
            today_str = f"'{today.strftime('%Y-%m-%d')}'"
            expanded = expanded.replace(":TODAY", today_str)
            macro_records.append((":TODAY", today_str))

        # Explicit user-supplied macros
        if macros:
            for k, v in macros.items():
                macro_key = f":{k}" if not k.startswith(":") else k
                val_str = str(v)
                if macro_key in expanded:
                    expanded = expanded.replace(macro_key, val_str)
                    macro_records.append((macro_key, val_str))

        return expanded, tuple(macro_records)

    def parse_query(
        self, query_text: str, macros: dict[str, Any] | None = None
    ) -> GarfQuerySpec:
        """Parse SQL query into structured fields, aliases, filters, sorts, and limits."""
        cleaned_text = query_text.strip()
        expanded_text, dynamic_macros = self._expand_macros(cleaned_text, macros)

        # Extract title from leading comment if present (e.g. /* title: campaign_perf */ or -- title: campaign_perf)
        title = None
        title_match = re.search(
            r"(?:/\*|--)\s*title:\s*([\w\-]+)", cleaned_text, re.IGNORECASE
        )
        if title_match:
            title = title_match.group(1).strip()

        # Normalize whitespace for SQL token extraction
        sql = re.sub(r"\s+", " ", expanded_text).strip()

        # Regular expression for SELECT ... FROM ... [WHERE ...] [ORDER BY ...] [LIMIT ...]
        select_match = re.search(
            r"SELECT\s+(.*?)\s+FROM\s+([a-zA-Z0-9_\.]+)(?:\s+WHERE\s+(.*?))?(?:\s+ORDER\s+BY\s+(.*?))?(?:\s+LIMIT\s+(\d+))?$",
            sql,
            re.IGNORECASE,
        )

        if not select_match:
            raise ValueError(f"Could not parse valid SQL from query: {cleaned_text}")

        raw_fields = select_match.group(1).strip()
        resource_name = select_match.group(2).strip()
        raw_where = select_match.group(3)
        raw_order = select_match.group(4)
        raw_limit = select_match.group(5)

        # Parse fields, aliases, and virtual columns
        field_tokens = [f.strip() for f in raw_fields.split(",") if f.strip()]
        fields: list[str] = []
        column_names: list[str] = []
        virtual_columns: list[VirtualColumnSpec] = []

        for token in field_tokens:
            alias_match = re.search(r"^(.*?)\s+(?:AS|as)\s+([a-zA-Z0-9_]+)$", token)
            if alias_match:
                expr = alias_match.group(1).strip()
                alias = alias_match.group(2).strip()
                fields.append(expr)
                column_names.append(alias)
                if re.search(r"[\/\*\+\-\(\)\'\"]", expr) or re.search(r"\d+", expr):
                    src_candidates = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\.]*", expr)
                    src_fields = [
                        c
                        for c in src_candidates
                        if c.upper()
                        not in (
                            "AS",
                            "NULL",
                            "TRUE",
                            "FALSE",
                            "CASE",
                            "WHEN",
                            "THEN",
                            "ELSE",
                            "END",
                        )
                    ]
                    virtual_columns.append(
                        VirtualColumnSpec(
                            name=alias,
                            expression=expr,
                            source_fields=tuple(dict.fromkeys(src_fields)),
                        )
                    )
            else:
                fields.append(token)
                col_name = token.split(".")[-1]
                column_names.append(col_name)

        # Parse filters
        filters: list[str] = []
        if raw_where:
            filters = [
                f.strip()
                for f in re.split(r"\s+AND\s+", raw_where, flags=re.IGNORECASE)
                if f.strip()
            ]

        # Parse sorts
        sorts: list[str] = []
        if raw_order:
            sorts = [s.strip() for s in raw_order.split(",") if s.strip()]

        limit = int(raw_limit) if raw_limit else None

        return GarfQuerySpec(
            text=cleaned_text,
            title=title or resource_name,
            resource_name=resource_name,
            fields=tuple(fields),
            filters=tuple(filters),
            sorts=tuple(sorts),
            limit=limit,
            column_names=tuple(column_names),
            dynamic_macros=dynamic_macros,
            virtual_columns=tuple(virtual_columns),
        )

    def simulate_report(
        self, query_spec: GarfQuerySpec, row_count: int = 5, seed: int = 42
    ) -> GarfReportBatch:
        """Generate deterministic synthetic rows matching column specifications."""
        effective_count = (
            min(row_count, query_spec.limit) if query_spec.limit else row_count
        )
        rows: list[tuple[Any, ...]] = []
        vc_by_name = {vc.name: vc for vc in query_spec.virtual_columns}

        base_date = datetime.date(2026, 9, 1)

        for i in range(effective_count):
            row_vals: list[Any] = []
            for col in query_spec.column_names:
                col_lower = col.lower()
                vc = vc_by_name.get(col)
                if vc:
                    expr = vc.expression.strip()
                    if (expr.startswith("'") and expr.endswith("'")) or (
                        expr.startswith('"') and expr.endswith('"')
                    ):
                        row_vals.append(expr[1:-1])
                    elif "/" in expr:
                        parts = [p.strip() for p in expr.split("/")]
                        if len(parts) == 2 and parts[1].isdigit():
                            divisor = float(parts[1])
                            base_micros = 1_000_000 * (i + 1) + 250_000
                            row_vals.append(round(base_micros / divisor, 2))
                        elif "impression" in expr.lower():
                            row_vals.append(round(0.025 * (i + 1), 4))
                        else:
                            row_vals.append(round(1.5 * (i + 1), 2))
                    elif "*" in expr:
                        row_vals.append(round(2.5 * (i + 1), 2))
                    else:
                        row_vals.append(round(1.25 * (i + 1) + 0.5, 2))
                elif "id" in col_lower:
                    row_vals.append(1000 + i + (seed % 100))
                elif any(
                    k in col_lower for k in ("click", "impression", "view", "count")
                ):
                    row_vals.append(100 * (i + 1) + (seed % 50))
                elif any(
                    k in col_lower
                    for k in ("cost", "cpc", "ctr", "rate", "spend", "value")
                ):
                    row_vals.append(round(1.25 * (i + 1) + 0.5, 2))
                elif any(k in col_lower for k in ("date", "day")):
                    d = base_date + datetime.timedelta(days=i)
                    row_vals.append(d.isoformat())
                elif "status" in col_lower:
                    row_vals.append("ACTIVE" if i % 2 == 0 else "PAUSED")
                elif "name" in col_lower:
                    row_vals.append(f"{query_spec.resource_name}_{col}_{i + 1}")
                else:
                    row_vals.append(f"val_{col}_{i + 1}")
            rows.append(tuple(row_vals))

        return GarfReportBatch(
            column_names=query_spec.column_names,
            rows=tuple(rows),
            row_count=len(rows),
            query_title=query_spec.title,
        )

    def write_report(
        self, report: GarfReportBatch, destination_type: str, destination_path: str
    ) -> GarfExecutionReceipt:
        """Write tabular report batch to target storage."""
        start_time = time.monotonic()
        dest_type = destination_type.lower().strip()
        path = Path(destination_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if dest_type == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(report.column_names)
                for row in report.rows:
                    writer.writerow(row)
            details = (
                ("format", "csv"),
                ("path", str(path)),
                ("rows", str(report.row_count)),
            )

        elif dest_type == "json":
            records = report.to_dict_list()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            details = (
                ("format", "json"),
                ("path", str(path)),
                ("rows", str(report.row_count)),
            )

        elif dest_type in ("sqlite", "duckdb"):
            # Standard SQLite storage table named after query_title or 'garf_report'
            table_name = report.query_title or "garf_report"
            table_name = re.sub(r"[^\w]", "_", table_name)
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()

            # Infer column storage affinity from rows: INTEGER, REAL, or TEXT
            col_types: list[str] = []
            for col_idx, col in enumerate(report.column_names):
                sample_vals = [
                    r[col_idx] for r in report.rows if r[col_idx] is not None
                ]
                if sample_vals and all(
                    isinstance(v, int) and not isinstance(v, bool) for v in sample_vals
                ):
                    col_types.append(f'"{col}" INTEGER')
                elif sample_vals and all(
                    isinstance(v, (int, float)) and not isinstance(v, bool)
                    for v in sample_vals
                ):
                    col_types.append(f'"{col}" REAL')
                else:
                    col_types.append(f'"{col}" TEXT')

            cols_def = ", ".join(col_types)
            cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_def})')
            placeholders = ", ".join("?" for _ in report.column_names)
            cursor.executemany(
                f'INSERT INTO "{table_name}" VALUES ({placeholders})',
                [tuple(r) for r in report.rows],
            )
            conn.commit()
            conn.close()
            details = (
                ("format", dest_type),
                ("path", str(path)),
                ("table", table_name),
                ("rows", str(report.row_count)),
            )

        elif dest_type == "console":
            lines = [" | ".join(report.column_names), "-" * 40]
            for row in report.rows:
                lines.append(" | ".join(str(val) for val in row))
            table_str = "\n".join(lines)
            details = (("format", "console"), ("preview", table_str[:500]))

        else:
            raise ValueError(f"Unsupported destination_type: {destination_type}")

        elapsed = time.monotonic() - start_time
        return GarfExecutionReceipt(
            status="ok",
            operation=f"write_{dest_type}",
            row_count=report.row_count,
            elapsed_seconds=round(elapsed, 4),
            details=details,
        )

    def execute_query(
        self,
        query_text: str,
        destination_type: str | None = None,
        destination_path: str | None = None,
        macros: dict[str, Any] | None = None,
    ) -> GarfReportBatch:
        """Parse query, simulate/fetch report, and optionally write to destination."""
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
        """Execute a DAG of query extraction and post-processing steps."""
        start_time = time.monotonic()
        context = dict(context_params or {})
        executed_steps: list[str] = []
        total_rows = 0

        # Step dependency topological traversal
        remaining = {s.step_id: s for s in steps}
        completed: set[str] = set()

        while remaining:
            runnable = [
                s
                for s in remaining.values()
                if all(dep in completed for dep in s.depends_on)
            ]
            if not runnable:
                missing = [s.step_id for s in remaining.values()]
                raise ValueError(
                    f"Cyclic or unsatisfied step dependencies detected: {missing}"
                )

            for step in runnable:
                self._logger.info(
                    "Executing workflow step",
                    step_id=step.step_id,
                    step_type=step.step_type,
                )
                if step.step_type == "query":
                    sql_text = step.sql_query
                    if not sql_text and step.query_path:
                        qpath = Path(step.query_path)
                        if qpath.exists():
                            sql_text = qpath.read_text(encoding="utf-8")
                        else:
                            raise FileNotFoundError(
                                f"Query file not found for step {step.step_id}: {step.query_path}"
                            )

                    if not sql_text:
                        raise ValueError(
                            f"Step {step.step_id} of type 'query' has neither sql_query nor valid query_path"
                        )

                    report = self.execute_query(
                        sql_text,
                        destination_type=step.writer_type,
                        destination_path=step.destination,
                        macros=context,
                    )
                    total_rows += report.row_count
                    context[f"{step.step_id}_rows"] = report.row_count
                    context[f"{step.step_id}_columns"] = list(report.column_names)
                    context[f"{step.step_id}_report"] = report

                elif step.step_type == "sql" and step.sql_query and step.destination:
                    # Expand context macros in post-processing SQL query
                    sql_to_run, _ = self._expand_macros(step.sql_query, macros=context)
                    conn = sqlite3.connect(step.destination)
                    cur = conn.cursor()
                    cur.execute(sql_to_run)
                    if sql_to_run.strip().upper().startswith("SELECT"):
                        fetched = cur.fetchall()
                        context[f"{step.step_id}_rows"] = len(fetched)
                    elif cur.rowcount >= 0:
                        context[f"{step.step_id}_rows"] = cur.rowcount
                    conn.commit()
                    conn.close()

                elif (
                    step.step_type == "writer" and step.destination and step.writer_type
                ):
                    # Export data from context or staging DB to destination file
                    src_db = step.query_path or context.get("staging_db")
                    prev_report = None
                    for dep in step.depends_on:
                        if f"{dep}_report" in context:
                            prev_report = context[f"{dep}_report"]
                            break

                    if prev_report is not None:
                        receipt = self.write_report(
                            prev_report, step.writer_type, step.destination
                        )
                        total_rows += receipt.row_count
                    elif src_db and Path(src_db).exists():
                        conn = sqlite3.connect(src_db)
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1"
                        )
                        table_row = cur.fetchone()
                        if table_row:
                            tname = table_row[0]
                            cur.execute(f'SELECT * FROM "{tname}"')
                            col_names = tuple(desc[0] for desc in cur.description)
                            rows = tuple(cur.fetchall())
                            batch = GarfReportBatch(
                                column_names=col_names,
                                rows=rows,
                                row_count=len(rows),
                                query_title=tname,
                            )
                            receipt = self.write_report(
                                batch, step.writer_type, step.destination
                            )
                            total_rows += receipt.row_count
                        conn.close()

                completed.add(step.step_id)
                executed_steps.append(step.step_id)
                del remaining[step.step_id]

        elapsed = time.monotonic() - start_time
        return GarfExecutionReceipt(
            status="ok",
            operation="run_workflow",
            row_count=total_rows,
            elapsed_seconds=round(elapsed, 4),
            details=(
                ("executed_steps", ",".join(executed_steps)),
                ("step_count", str(len(executed_steps))),
            ),
        )
