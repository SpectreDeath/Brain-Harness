"""Rollout and stage concurrency execution helpers for task-level recursion.

Distilled from google-research/harness2 `core.recursion`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import structlog

from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.ledger import BudgetLedger
from harness.services.recursive_harnessing.models import ModeResult, RunView, Stage, Tree
from harness.services.recursive_harnessing.protocols import TaskAdapter

logger = structlog.get_logger(__name__)
PHASE_WIDTH = 2
RunIdOf = Callable[[str], str]


def roll(
    adapter: TaskAdapter,
    task_id: str,
    label: str,
    tree: Tree | None,
    run_id_of: RunIdOf,
    work_dir: Path,
) -> RunView:
    """Materialise a harness and roll it once. A dead rollout is recorded, never raised."""
    hdir = S.write_tree(adapter.surface, tree, work_dir / "harnesses" / label) if tree is not None else None
    run_id = run_id_of(label)
    try:
        rd = Path(adapter.execute(task_id, hdir, run_id))
        exists = rd.exists()
        return RunView(
            label,
            run_id,
            rd,
            exists,
            exists and adapter.delivered(rd),
            error="" if exists else "adapter returned a missing run directory",
        )
    except Exception as exc:  # a failed rollout is data for the next stage
        logger.warning("rollout_failed", label=label, error=str(exc))
        return RunView(label, run_id, work_dir / "missing", False, False, error=f"{type(exc).__name__}: {exc}")


def _roll_many(
    adapter: TaskAdapter,
    ledger: BudgetLedger,
    task_id: str,
    items: Sequence[tuple[str, Tree]],
    run_id_of: RunIdOf,
    work_dir: Path,
    width: int,
) -> dict[str, RunView]:
    """Roll independent harnesses concurrently, then record them in the caller's order."""
    if not items:
        return {}
    n = max(1, min(len(items), width))
    with ThreadPoolExecutor(max_workers=n) as pool:
        got = list(pool.map(lambda it: roll(adapter, task_id, it[0], it[1], run_id_of, work_dir), items))
    out: dict[str, RunView] = {}
    for (label, _), rv in zip(items, got):
        ledger.rollout(label)
        out[label] = rv
    return out


def _stages(specs: Sequence[tuple], make: Callable[[tuple], Stage], workers: int) -> list[Stage]:
    with ThreadPoolExecutor(max_workers=max(1, min(len(specs), workers))) as pool:
        return list(pool.map(make, specs))


def _absorb(result: ModeResult, ledger: BudgetLedger, stages: Sequence[Stage]) -> None:
    for st in stages:
        ledger.session(st.label, st.usd, cached=st.cached, attempts=st.attempts)
        result.stages.append(st)
        result.trees[st.label] = st.tree


def _begin(mode: str, task_id: str, k: int, base: Sequence[RunView]) -> tuple[ModeResult, BudgetLedger]:
    ledger = BudgetLedger(mode=mode, task_id=task_id, k=k)
    for rv in base:
        ledger.rollout(rv.label)
    result = ModeResult(mode=mode, task_id=task_id, k=k, ledger=ledger)
    result.rollouts.update({rv.label: rv for rv in base})
    return result, ledger


def _notes(stages: Sequence[Stage]) -> dict[str, str]:
    return {s.label: s.notes or s.error for s in stages}

