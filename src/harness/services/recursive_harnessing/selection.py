"""Blind selection: choose one finished artifact among anonymised, label-shuffled candidates.

Distilled from google/harness2 `core.selection`. The selector sees *artifacts only* -- never
harnesses, run labels or provenance -- under arbitrary ids that are stable across reruns
(seeded shuffle). Non-answers are dropped before anonymising and the drop is recorded. A
selector failure degrades to a neutral fallback and never raises; an adapter/leak bug does
raise, because that is a defect and not a selection outcome.
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path

import structlog

from harness.services.recursive_harnessing.errors import SelectorError
from harness.services.recursive_harnessing.guards import assert_no_verdicts
from harness.services.recursive_harnessing.models import RunView, Selection
from harness.services.recursive_harnessing.protocols import CandidateSelector, TaskAdapter

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


def selection_pool(mode: str, k: int, rollouts: dict[str, RunView], base: Sequence[RunView]) -> dict[str, RunView]:
    """Exactly the k finals of `mode`: agg1..aggk (parallel) or c1..ck (sequential).

    `base` is accepted and deliberately unused: the reference executions are excluded so
    there is no abstention by construction, and the call site shows that exclusion.
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


def blind_select(
    task_id: str,
    k: int,
    mode: str,
    candidates: dict[str, RunView],
    *,
    adapter: TaskAdapter,
    selector: CandidateSelector,
    work_dir: Path | str,
    pool_kind: str = "finals",
) -> Selection:
    """Pick one output blind. `pool_kind="finals"` falls back to the first final on selector
    failure; `"mixed"` (base executions in the pool) falls back only to a delivered base."""
    if pool_kind not in ("finals", "mixed"):
        raise ValueError(f"unknown pool_kind {pool_kind!r}; expected 'finals' or 'mixed'")
    head = {"task_id": task_id, "mode": mode, "k": k}
    dropped: list[str] = []
    pool, texts = _render_pool(candidates, adapter, dropped)
    if not pool:
        return Selection(**head, dropped=tuple(dropped), error="no candidate produced an artifact")
    id_map = assign_ids(list(pool), task_id=task_id, k=k, mode=mode)
    root = Path(work_dir) / "selection" / f"{mode}{k}"
    shutil.rmtree(root, ignore_errors=True)
    (root / "candidates").mkdir(parents=True)
    task_text = adapter.task_prompt(task_id)
    (root / "task.md").write_text(task_text, encoding="utf-8")
    anon_texts = {anon: texts[lbl] for anon, lbl in id_map.items()}
    for anon, text in anon_texts.items():
        (root / "candidates" / f"{anon}.md").write_text(text, encoding="utf-8")
    assert_no_verdicts(root)  # raises on a leak: a defect, not a selection outcome

    usd, why, error, fallback, chosen_id = 0.0, "", "", False, ""
    try:
        choice = selector.choose(task_text, anon_texts)
        usd += choice.cost_usd
        if choice.anon_id not in id_map:
            raise ValueError(f"chose {choice.anon_id!r}, which is not one of {', '.join(sorted(id_map))}")
        chosen_id, why = choice.anon_id, choice.why[:2000]
    except (SelectorError, ValueError) as exc:
        usd += getattr(exc, "cost_usd", 0.0)
        label = _fallback_label(pool, pool_kind)
        if label is None:
            return Selection(
                **head,
                id_map=id_map,
                dropped=tuple(dropped),
                n_candidates=len(pool),
                usd=usd,
                error=f"{str(exc)[:350]}; no delivered base artifact for a neutral fallback",
            )
        chosen_id = next(a for a, lbl in id_map.items() if lbl == label)
        fallback, error = True, str(exc)[:400]
    label = id_map[chosen_id]
    sel = Selection(
        **head,
        chosen_id=chosen_id,
        chosen_label=label,
        chosen_run_id=pool[label].run_id,
        chosen_is_base=_is_base(label),
        why=why,
        id_map=id_map,
        dropped=tuple(dropped),
        n_candidates=len(pool),
        ok=True,
        fallback=fallback,
        error=error,
        usd=usd,
    )
    return _persist(sel, root, str(pool[label].run_dir))


def trivial_selection(
    task_id: str,
    k: int,
    mode: str,
    candidates: dict[str, RunView],
    *,
    adapter: TaskAdapter,
    work_dir: Path | str,
) -> Selection:
    """Deliver the single k=1 final without a selector session (same non-answer drop rules)."""
    if len(candidates) > 1:
        raise ValueError(f"trivial_selection expects at most one candidate, got {sorted(candidates)}")
    head = {"task_id": task_id, "mode": mode, "k": k}
    dropped: list[str] = []
    pool, _ = _render_pool(candidates, adapter, dropped)
    if not pool:
        return Selection(
            **head,
            trivial=True,
            dropped=tuple(dropped),
            error="no candidate produced an artifact (finals-only pool has no base fallback)",
        )
    label = next(iter(pool))
    sel = Selection(
        **head,
        chosen_id="A",
        chosen_label=label,
        chosen_run_id=pool[label].run_id,
        chosen_is_base=_is_base(label),
        id_map={"A": label},
        n_candidates=1,
        ok=True,
        trivial=True,
        dropped=tuple(dropped),
        why="trivial pool: single final at k=1; delivered without a selector session",
    )
    root = Path(work_dir) / "selection" / f"{mode}{k}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return _persist(sel, root, str(pool[label].run_dir))
