"""Zero-network deterministic tabular report simulation."""

from __future__ import annotations

import datetime
from typing import Any

from .models import GarfQuerySpec, GarfReportBatch


def simulate_report(
    query_spec: GarfQuerySpec, row_count: int = 5, seed: int = 42
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
