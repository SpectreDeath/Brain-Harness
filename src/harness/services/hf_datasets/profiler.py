"""Schema profiling, dataset inspection, sampling, and storage strategy evaluation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .models import HfColumnSchema, HfDatasetMetadata, HfStorageStrategy
from .streamer import iter_records, probe_file_streaming


def inspect_dataset(
    path_or_name: str, split: str | None = None
) -> HfDatasetMetadata:
    """Inspect schema, splits, and features without downloading or loading entire dataset."""
    p = Path(path_or_name)
    active_split = split or "train"

    if p.exists():
        if p.is_file():
            byte_size = p.stat().st_size
            ext = p.suffix.lower().lstrip(".")
            features, num_rows = probe_file_streaming(p)
            return HfDatasetMetadata(
                name=p.stem,
                split=active_split,
                num_rows=num_rows,
                features=features,
                format=ext or "arrow",
                byte_size=byte_size,
                is_streaming=False,
            )
        else:
            # Directory of partitions/files
            files = [f for f in p.rglob("*") if f.is_file()]
            byte_size = sum(f.stat().st_size for f in files)
            features: dict[str, str] = {}
            total_rows = 0
            for f in files[:5]:
                f_feats, f_rows = probe_file_streaming(f)
                features.update(f_feats)
                total_rows += f_rows
            return HfDatasetMetadata(
                name=p.name,
                split=active_split,
                num_rows=total_rows,
                features=features or {"directory": "dataset_folder"},
                format="dataset_folder",
                byte_size=byte_size,
                is_streaming=False,
            )

    # External remote or simulated hub dataset
    return HfDatasetMetadata(
        name=path_or_name,
        split=active_split,
        num_rows=0,
        features={"hub_dataset": "remote"},
        format="remote_stream",
        byte_size=0,
        is_streaming=True,
    )


def evaluate_storage_strategy(
    path_or_name: str,
    split: str | None = None,
    auto_stream_threshold_mb: int = 500,
) -> HfStorageStrategy:
    """Evaluate physical footprint and select between memory-mapped Arrow and streaming."""
    meta = inspect_dataset(path_or_name, split)
    threshold_bytes = auto_stream_threshold_mb * 1024 * 1024

    if meta.is_streaming or meta.byte_size > threshold_bytes:
        mb = meta.byte_size / (1024 * 1024)
        return HfStorageStrategy(
            strategy="lazy_stream",
            reason=(
                f"Dataset footprint ({mb:.1f} MB) exceeds auto-stream threshold "
                f"({auto_stream_threshold_mb} MB) or requires remote streaming."
            ),
            estimated_bytes=meta.byte_size,
            recommended_batch_size=100,
            recommended_workers=min(4, os.cpu_count() or 2),
            requires_streaming=True,
        )

    mb = meta.byte_size / (1024 * 1024)
    return HfStorageStrategy(
        strategy="mmap_arrow",
        reason=(
            f"Dataset footprint ({mb:.1f} MB) fits comfortably within memory threshold "
            f"({auto_stream_threshold_mb} MB); optimal for zero-copy random access."
        ),
        estimated_bytes=meta.byte_size,
        recommended_batch_size=500,
        recommended_workers=1,
        requires_streaming=False,
    )


def stream_sample(
    path_or_name: str, split: str = "train", max_samples: int = 10
) -> list[dict[str, Any]]:
    """Lazily sample N records without loading entire dataset into RAM."""
    records: list[dict[str, Any]] = []
    for row in iter_records(path_or_name, max_records=max_samples):
        records.append(row)
        if len(records) >= max_samples:
            break
    return records


def profile_schema(path_or_name: str) -> list[HfColumnSchema]:
    """Profile and return comprehensive column schemas and Arrow data types."""
    samples = stream_sample(path_or_name, max_samples=25)
    if not samples:
        return [HfColumnSchema(name="empty", arrow_type="null", is_nullable=True)]

    columns: dict[str, list[Any]] = {}
    for row in samples:
        for k, v in row.items():
            columns.setdefault(k, []).append(v)

    schemas: list[HfColumnSchema] = []
    for col_name, vals in columns.items():
        non_null = [v for v in vals if v is not None]
        arrow_type = "string"
        if non_null:
            first = non_null[0]
            if isinstance(first, bool):
                arrow_type = "bool"
            elif isinstance(first, int):
                arrow_type = "int64"
            elif isinstance(first, float):
                arrow_type = "double"
            elif isinstance(first, dict):
                arrow_type = "struct"
            elif isinstance(first, (list, tuple)):
                arrow_type = "list"

        feature_type = "Sequence" if arrow_type in ("struct", "list") else "Value"
        schemas.append(
            HfColumnSchema(
                name=col_name,
                arrow_type=arrow_type,
                is_nullable=len(non_null) < len(vals),
                feature_type=feature_type,
                sample_values=tuple(vals[:3]),
            )
        )

    return schemas
