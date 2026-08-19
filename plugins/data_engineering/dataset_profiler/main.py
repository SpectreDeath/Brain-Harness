"""Tabular dataset profiler, Z-score outlier detector, and correlation matrix plugin."""

from __future__ import annotations

import math
from typing import Any


def profile_tabular_dataset(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute rich tabular statistics across all columns."""
    if not records:
        return {"status": "ok", "row_count": 0, "columns_count": 0, "columns": {}}

    cols = list(records[0].keys())
    report: dict[str, Any] = {}

    for c in cols:
        vals = [r.get(c) for r in records if r.get(c) is not None]
        null_cnt = len(records) - len(vals)
        unique_cnt = len({str(v) for v in vals})

        num_vals: list[float] = []
        for v in vals:
            try:
                num_vals.append(float(v))
            except (ValueError, TypeError):
                pass

        is_num = len(num_vals) == len(vals) and len(vals) > 0
        col_meta: dict[str, Any] = {
            "total": len(records),
            "valid": len(vals),
            "nulls": null_cnt,
            "null_ratio": round(null_cnt / len(records), 4),
            "uniques": unique_cnt,
            "is_numeric": is_num,
        }

        if is_num and num_vals:
            col_meta["min"] = min(num_vals)
            col_meta["max"] = max(num_vals)
            col_meta["mean"] = round(sum(num_vals) / len(num_vals), 4)

        report[c] = col_meta

    return {
        "status": "ok",
        "row_count": len(records),
        "columns_count": len(cols),
        "columns": report,
    }


def detect_outliers_zscore(values: list[float], threshold: float = 3.0) -> dict[str, Any]:
    """Identify outliers in a list of numbers using the Z-score method."""
    if len(values) < 3:
        return {"status": "ok", "outliers_count": 0, "outliers": []}

    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    outliers: list[dict[str, Any]] = []
    if std_dev > 0:
        for idx, val in enumerate(values):
            z = (val - mean) / std_dev
            if abs(z) >= threshold:
                outliers.append({
                    "index": idx,
                    "value": val,
                    "z_score": round(z, 2),
                })

    return {
        "status": "ok",
        "total_values": n,
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "threshold": threshold,
        "outliers_count": len(outliers),
        "outliers": outliers,
    }


def compute_correlation_matrix(
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """Compute Pearson correlation matrix between numerical columns."""
    if not records:
        return {"status": "ok", "matrix": {}}

    target_cols = columns or [
        k for k, v in records[0].items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]

    matrix: dict[str, dict[str, float]] = {c1: {} for c1 in target_cols}

    for c1 in target_cols:
        for c2 in target_cols:
            vals1 = [float(r[c1]) for r in records if c1 in r and c2 in r]
            vals2 = [float(r[c2]) for r in records if c1 in r and c2 in r]

            if len(vals1) < 2 or len(vals2) < 2:
                matrix[c1][c2] = 0.0
                continue

            n = len(vals1)
            m1 = sum(vals1) / n
            m2 = sum(vals2) / n

            cov = sum((x - m1) * (y - m2) for x, y in zip(vals1, vals2, strict=False))
            std1 = math.sqrt(sum((x - m1) ** 2 for x in vals1))
            std2 = math.sqrt(sum((y - m2) ** 2 for y in vals2))

            if std1 > 0 and std2 > 0:
                corr = cov / (std1 * std2)
                matrix[c1][c2] = round(corr, 4)
            else:
                matrix[c1][c2] = 1.0 if c1 == c2 else 0.0

    return {
        "status": "ok",
        "columns": target_cols,
        "matrix": matrix,
    }
