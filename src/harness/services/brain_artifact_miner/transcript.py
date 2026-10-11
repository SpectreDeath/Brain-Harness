"""Transcript indexing and O(1) binary byte-offset seek retrieval (Rule 22, Rule 48)."""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger("harness.services.brain_artifact_miner.transcript")


def build_offset_index(
    path: Path,
    cache: dict[Path, dict[int, tuple[int, int]]] | None = None,
) -> dict[int, tuple[int, int]]:
    """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48).

    Scans the file once in binary mode ('rb') to map step indices to
    (byte_offset, byte_length) pairs, enabling sub-millisecond seek retrieval.
    """
    path = path.resolve()
    if cache is not None and path in cache:
        return cache[path]

    index: dict[int, tuple[int, int]] = {}
    if not path.exists():
        return index

    with open(path, "rb") as f:
        offset = 0
        step_idx = 0
        for line in f:
            length = len(line)
            try:
                line_str = line.decode("utf-8", errors="ignore")
                m = re.search(r'"step_index"\s*:\s*(\d+)', line_str)
                if m:
                    idx = int(m.group(1))
                else:
                    idx = step_idx
                index[idx] = (offset, length)
            except Exception:
                index[step_idx] = (offset, length)
            offset += length
            step_idx += 1

    if cache is not None:
        cache[path] = index
    return index


def get_step(
    transcript_path: Path,
    step_index: int,
    dereference_truncated: bool = True,
    cache: dict[Path, dict[int, tuple[int, int]]] | None = None,
) -> dict[str, Any] | None:
    """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48)."""
    transcript_path = transcript_path.resolve()
    index = build_offset_index(transcript_path, cache=cache)
    if step_index not in index:
        return None

    offset, length = index[step_index]
    try:
        with open(transcript_path, "rb") as f:
            f.seek(offset)
            raw_bytes = f.read(length)
            step_data: dict[str, Any] = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
    except Exception as ex:
        logger.warning("Error reading step %d from %s: %s", step_index, transcript_path, ex)
        return None

    # Check for truncation dereferencing (Rule 22)
    if dereference_truncated and step_data.get("is_truncated") is True:
        full_path = transcript_path.parent / "transcript_full.jsonl"
        if full_path.exists() and full_path != transcript_path:
            full_step = get_step(full_path, step_index, dereference_truncated=False, cache=cache)
            if full_step is not None:
                step_data["content"] = full_step.get("content", step_data.get("content", ""))
                step_data["tool_calls"] = full_step.get("tool_calls") or step_data.get("tool_calls") or []
                step_data["is_truncated"] = False
                step_data["dereferenced"] = True
                return step_data

    step_data.setdefault("dereferenced", False)
    return step_data


def stream_steps(
    transcript_path: Path,
    dereference_truncated: bool = True,
    cache: dict[Path, dict[int, tuple[int, int]]] | None = None,
) -> Iterator[dict[str, Any]]:
    """Stream all transcript steps with optional truncation dereferencing."""
    transcript_path = transcript_path.resolve()
    index = build_offset_index(transcript_path, cache=cache)
    for idx in sorted(index.keys()):
        step = get_step(transcript_path, idx, dereference_truncated=dereference_truncated, cache=cache)
        if step is not None:
            yield step


__all__ = [
    "build_offset_index",
    "get_step",
    "stream_steps",
]
