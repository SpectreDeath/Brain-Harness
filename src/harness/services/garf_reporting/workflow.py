"""Topological DAG workflow execution for multi-step Garf reporting pipelines."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from .models import GarfExecutionReceipt, GarfReportBatch, GarfWorkflowStep
from .parser import expand_macros

if TYPE_CHECKING:
    from .models import GarfReportingService

logger = structlog.get_logger(__name__)


def run_workflow_dag(
    service: GarfReportingService,
    steps: list[GarfWorkflowStep],
    context_params: dict[str, Any] | None = None,
) -> GarfExecutionReceipt:
    """Execute a DAG of query extraction and post-processing steps."""
    start_time = time.monotonic()
    context = dict(context_params or {})
    executed_steps: list[str] = []
    total_rows = 0

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
            logger.info(
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

                report = service.execute_query(
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
                sql_to_run, _ = expand_macros(step.sql_query, macros=context)
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
                src_db = step.query_path or context.get("staging_db")
                prev_report = None
                for dep in step.depends_on:
                    if f"{dep}_report" in context:
                        prev_report = context[f"{dep}_report"]
                        break

                if prev_report is not None:
                    receipt = service.write_report(
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
                        receipt = service.write_report(
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
