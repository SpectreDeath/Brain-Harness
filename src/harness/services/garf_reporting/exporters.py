"""Multi-destination report egress writers (CSV, JSON, SQLite, Console)."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import time
from pathlib import Path

from .models import GarfExecutionReceipt, GarfReportBatch


def write_report(
    report: GarfReportBatch, destination_type: str, destination_path: str
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
        table_name = report.query_title or "garf_report"
        table_name = re.sub(r"[^\w]", "_", table_name)
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()

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
