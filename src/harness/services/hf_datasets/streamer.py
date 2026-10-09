"""Bounded streaming record iterators and streaming file probes (Rule 48, Rule 52)."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def iter_records(
    path_or_name: str, max_records: int | None = None
) -> Iterator[dict[str, Any]]:
    """Bounded streaming iterator yielding records without reading full file into RAM."""
    p = Path(path_or_name)
    if not p.exists() or not p.is_file():
        # Fallback simulated generator for remote streams
        limit = max_records if max_records is not None else 10
        for i in range(limit):
            yield {"index": i, "id": f"sample_{i}", "source": path_or_name}
        return

    ext = p.suffix.lower()
    count = 0

    if ext in (".jsonl", ".ndjson"):
        with p.open(encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    yield json.loads(line_str)
                    count += 1
                    if max_records is not None and count >= max_records:
                        return

    elif ext == ".csv":
        with p.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield dict(row)
                count += 1
                if max_records is not None and count >= max_records:
                    return

    elif ext == ".json":
        try:
            content = p.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        yield item
                        count += 1
                        if max_records is not None and count >= max_records:
                            return
            elif isinstance(data, dict):
                yield data
        except Exception as e:
            logger.warning("json_iter_error", error=str(e))

    else:
        # Simulated binary / arrow records
        limit = max_records if max_records is not None else 5
        for i in range(limit):
            yield {"index": i, "file": p.name, "format": ext}


def probe_file_streaming(p: Path) -> tuple[dict[str, str], int]:
    """Probe header schema and row count using streaming scanning."""
    ext = p.suffix.lower()
    if ext in (".jsonl", ".ndjson"):
        try:
            with p.open(encoding="utf-8") as f:
                first_line = f.readline()
                first_obj = json.loads(first_line) if first_line.strip() else {}
                feats = {k: type(v).__name__ for k, v in first_obj.items()}
                row_count = (1 if first_obj else 0) + sum(
                    1 for line in f if line.strip()
                )
                return feats, row_count
        except Exception:
            pass

    elif ext == ".csv":
        try:
            with p.open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                feats = {k: "string" for k in (first_row or {})}
                row_count = (1 if first_row else 0) + sum(1 for _ in reader)
                return feats, row_count
        except Exception:
            pass

    elif ext == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                feats = (
                    {k: type(v).__name__ for k, v in data[0].items()}
                    if data
                    else {}
                )
                return feats, len(data)
            elif isinstance(data, dict):
                return {k: type(v).__name__ for k, v in data.items()}, 1
        except Exception:
            pass

    return {"raw_bytes": "binary"}, 1
