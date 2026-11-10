"""Task-level recursion: Propose-Probe-Compose in parallel (WIDTH) and sequential (DEPTH) modes.

Distilled from google/harness2 `core.recursion`. Each mode schedules R = 4k rollouts and
P = 3k improvement stages (shared base executions included):

    parallel   : 2k i.i.d. candidates (INV, DOM) from shared evidence, then k INDEPENDENT compositions
    sequential : k nested rounds over the same shared base evidence; each round composes a checkpoint

Concurrency is real (thread pools) but the ledger is written *after* each pool drains, in the
caller's order, so a concurrent run records the same label sequence as a serial one. A dead
rollout is recorded, never raised.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import structlog

from harness.services.recursive_harnessing import prompts
from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.ledger import BudgetLedger
from harness.services.recursive_harnessing.models import ModeResult, RunView, Stage, Tree
from harness.services.recursive_harnessing.protocols import HarnessProposer, TaskAdapter
from harness.services.recursive_harnessing.stage import run_stage

logger = structlog.get_logger(__name__)
PHASE_WIDTH = 2
RunIdOf = Callable[[str], str]


def roll(
    adapter: TaskAdapter, task_id: str, label: str, tree: Tree | None, run_id_of: RunIdOf, work_dir: Path
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


def run_parallel(
    task_id: str,
    k: int,
    base: Sequence[RunView],
    *,
    adapter: TaskAdapter,
    proposer: HarnessProposer,
    work_dir: Path | str,
    run_id_of: RunIdOf,
    base_tree: Tree,
    library_dir: Path | None = None,
    propose_workers: int = PHASE_WIDTH,
    rollout_workers: int = PHASE_WIDTH,
) -> ModeResult:
    """WIDTH: 2k i.i.d. candidates from shared evidence, then k INDEPENDENT compositions."""
    spec, wd = adapter.surface, Path(work_dir)
    result, ledger = _begin("agg", task_id, k, base)
    base_dir = S.write_tree(spec, base_tree, wd / "harnesses" / "base")
    common = dict(
        fallback=base_tree,
        adapter=adapter,
        proposer=proposer,
        ctx_dir=wd / "context",
        task_id=task_id,
        rollouts=base,
        harness_dir=base_dir,
        library_dir=library_dir,
    )
    kw = dict(work=adapter.work, deliverable=adapter.deliverable)

    cands = _stages(
        [(f"{d.lower()}{i}", d, i) for i in range(1, k + 1) for d in ("INV", "DOM")],
        lambda s: run_stage(label=s[0], dim=s[1], job=prompts.propose(spec, s[1], k=k, index=s[2], **kw), **common),
        propose_workers,
    )
    _absorb(result, ledger, cands)
    result.rollouts.update(
        _roll_many(adapter, ledger, task_id, [(s.label, s.tree) for s in cands], run_id_of, wd, rollout_workers)
    )
    pool_ev = [(s.label, wd / "harnesses" / s.label, result.rollouts.get(s.label)) for s in cands]

    finals = _stages(
        [f"agg{i}" for i in range(1, k + 1)],
        lambda lbl: run_stage(
            label=lbl,
            dim="AGG",
            job=prompts.aggregate(spec, work=adapter.work, k=k, index=int(lbl[3:])),
            pool=pool_ev,
            decisions=_notes(cands),
            **common,
        ),
        propose_workers,
    )
    _absorb(result, ledger, finals)
    result.finals = [s.label for s in finals]
    result.rollouts.update(
        _roll_many(adapter, ledger, task_id, [(s.label, s.tree) for s in finals], run_id_of, wd, rollout_workers)
    )
    result.similarity = S.diversity({s.label: s.tree for s in finals})
    ledger.assert_identity()
    return result


def run_sequential(
    task_id: str,
    k: int,
    base: Sequence[RunView],
    *,
    adapter: TaskAdapter,
    proposer: HarnessProposer,
    work_dir: Path | str,
    run_id_of: RunIdOf,
    base_tree: Tree,
    library_dir: Path | None = None,
    propose_workers: int = PHASE_WIDTH,
    rollout_workers: int = PHASE_WIDTH,
) -> ModeResult:
    """DEPTH: k nested passes over the same shared base evidence."""
    spec, wd = adapter.surface, Path(work_dir)
    result, ledger = _begin("seq", task_id, k, base)
    kw = dict(work=adapter.work, deliverable=adapter.deliverable)
    current: Tree = dict(base_tree)
    history: list[tuple[str, Path, RunView | None]] = []
    for t in range(1, k + 1):
        cur_dir = S.write_tree(spec, current, wd / "harnesses" / (f"c{t - 1}" if t > 1 else "base"))
        common = dict(
            fallback=current,
            adapter=adapter,
            proposer=proposer,
            ctx_dir=wd / "context",
            task_id=task_id,
            rollouts=base,
            harness_dir=cur_dir,
            library_dir=library_dir,
        )
        prior = _notes(result.stages)
        cands = _stages(
            [(f"inv{t}", "INV"), (f"dom{t}", "DOM")],
            lambda s: run_stage(
                label=s[0],
                dim=s[1],
                pool=list(history),
                decisions=prior,
                **common,
                job=prompts.propose(spec, s[1], k=k, index=t, round_t=(t if k > 1 else None), **kw),
            ),
            min(2, propose_workers),
        )
        _absorb(result, ledger, cands)
        result.rollouts.update(
            _roll_many(adapter, ledger, task_id, [(s.label, s.tree) for s in cands], run_id_of, wd, rollout_workers)
        )
        round_pool = list(history) + [
            (s.label, wd / "harnesses" / s.label, result.rollouts.get(s.label)) for s in cands
        ]
        job = (
            prompts.aggregate(spec, work=adapter.work, k=1, index=1)
            if k == 1
            else prompts.compose_round(spec, work=adapter.work, t=t, k=k)
        )
        comp = run_stage(
            label=f"c{t}", dim="COMPOSE", job=job, pool=round_pool, decisions=_notes(result.stages), **common
        )
        _absorb(result, ledger, [comp])
        rv = roll(adapter, task_id, comp.label, comp.tree, run_id_of, wd)
        ledger.rollout(comp.label)
        result.rollouts[comp.label] = rv
        history = round_pool + [(comp.label, wd / "harnesses" / comp.label, rv)]
        current = comp.tree
    result.finals = [f"c{i}" for i in range(1, k + 1)]
    ledger.assert_identity()
    return result


def run_mode(mode: str, *args, **kwargs) -> ModeResult:
    """Dispatch on the on-disk mode token: "agg" (parallel) or "seq" (sequential)."""
    if mode == "agg":
        return run_parallel(*args, **kwargs)
    if mode == "seq":
        return run_sequential(*args, **kwargs)
    raise ValueError(f"unknown mode {mode!r}; the method has exactly two: 'agg' (parallel) and 'seq' (sequential)")
