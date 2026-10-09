"""Dataset transformation, filtering, column projection, and mapping."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .lakehouse import write_records
from .models import HfTransformationSpec, HfTransformResult
from .streamer import iter_records


def transform_dataset(
    input_path: str, output_path: str, spec: HfTransformationSpec
) -> HfTransformResult:
    """Execute lazy filtering, column projection, and batched transformations."""
    t0 = time.perf_counter()
    in_p = Path(input_path)
    out_p = Path(output_path)

    if not in_p.exists():
        raise FileNotFoundError(f"Input file not found: {in_p}")

    out_p.parent.mkdir(parents=True, exist_ok=True)
    rename_map = dict(spec.rename_columns)

    def _matches(row: dict[str, Any]) -> bool:
        if not spec.filter_field or spec.filter_op is None:
            return True
        val = row.get(spec.filter_field)
        target = spec.filter_value
        op = spec.filter_op.lower()
        try:
            if op == "eq":
                return val == target
            if op == "neq":
                return val != target
            if op == "gt":
                return val > target
            if op == "gte":
                return val >= target
            if op == "lt":
                return val < target
            if op == "lte":
                return val <= target
            if op == "contains":
                return target in val if val is not None else False
            if op == "in":
                return val in target if target is not None else False
        except TypeError:
            return False
        return True

    processed_rows: list[dict[str, Any]] = []
    for raw_row in iter_records(str(in_p)):
        if not _matches(raw_row):
            continue

        row = dict(raw_row)
        if spec.select_columns:
            row = {k: row[k] for k in spec.select_columns if k in row}

        if rename_map:
            row = {rename_map.get(k, k): v for k, v in row.items()}

        processed_rows.append(row)

    fmt = out_p.suffix.lower().lstrip(".") or "jsonl"
    write_records(out_p, processed_rows, fmt)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    fingerprint = hashlib.sha256(
        f"{in_p.name}:{fmt}:{len(processed_rows)}:{spec.filter_field}:{spec.filter_op}".encode()
    ).hexdigest()[:16]

    return HfTransformResult(
        status="ok",
        rows_processed=len(processed_rows),
        execution_time_ms=round(elapsed_ms, 2),
        cache_fingerprint=fingerprint,
        output_path=str(out_p),
    )
