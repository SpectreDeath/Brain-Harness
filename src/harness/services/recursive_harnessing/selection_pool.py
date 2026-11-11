"""Candidate pool rendering, anonymised ID generation and selection persistence.

Distilled from google-research/harness2 `core.selection`.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path

import structlog

from harness.services.recursive_harnessing.models import RunView, Selection
from harness.services.recursive_harnessing.protocols import TaskAdapter

logger = structlog.get_logger(__name__)


def anon_id(index: int) -> str:
    """A..Z, AA..AZ, BA... -- bijective base-26, always a valid choice token."""
    out, n = "", int(index) + 1
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(ord("A") + rem) + out
    return out


def assign_ids(labels: Sequence[str], *, task_id: str, k: int, mode: str) -> dict[str, str]:
    """anon id -> label, by canonical sort then a seeded shuffle: stable across reruns."""
    seed = int(hashlib.sha1(f"{task_id}|{k}|{mode}".encode()).hexdigest()[:12], 16)
    ordered = sorted(labels)
    random.Random(seed).shuffle(ordered)
    return {anon_id(i): lbl for i, lbl in enumerate(ordered)}


def _is_base(label: str) -> bool:
    return label.startswith("base")


def selection_pool(
    mode: str, k: int, rollouts: dict[str, RunView], base: Sequence[RunView]
) -> dict[str, RunView]:
    """Exactly the k finals of `mode`: agg1..aggk (parallel) or c1..ck (sequential).

    `base` is accepted and deliberately unused: reference executions are excluded.
    """
    del base
    n = int(k)
    labels = [f"agg{i}" for i in range(1, n + 1)] if mode == "agg" else [f"c{i}" for i in range(1, n + 1)]
    return {lbl: rollouts[lbl] for lbl in labels if lbl in rollouts}


def _render_pool(
    candidates: dict[str, RunView], adapter: TaskAdapter, dropped: list[str]
) -> tuple[dict[str, RunView], dict[str, str]]:
    pool: dict[str, RunView] = {}
    texts: dict[str, str] = {}
    for lbl, rv in candidates.items():
        if not (rv.ok and rv.delivered):
            dropped.append(lbl)
            continue
        try:
            rendered = adapter.deliverable_text(rv.run_dir) or ""
        except Exception as exc:  # adapter render failure is evidence of a non-answer
            logger.warning("candidate_render_failed", label=lbl, error=str(exc))
            dropped.append(f"{lbl} (render failed: {type(exc).__name__}: {exc})"[:200])
            continue
        if not rendered.strip():
            dropped.append(lbl)
            continue
        pool[lbl], texts[lbl] = rv, rendered
    return pool, texts


def _fallback_label(pool: dict[str, RunView], pool_kind: str) -> str | None:
    """Neutral stand-in after a selector failure: a delivered base, else the first final."""
    base = sorted(lbl for lbl in pool if _is_base(lbl))
    if base:
        return base[0]
    return sorted(pool)[0] if pool_kind == "finals" else None


def _persist(sel: Selection, root: Path, run_dir: str) -> Selection:
    try:
        rec = asdict(sel) | {"chosen_run_dir": run_dir}
        (root / "selection.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    except OSError as exc:
        return replace(sel, ok=False, error=(sel.error + f" | could not persist selection: {exc}")[:400])
    return sel

