"""The evidence tree a proposer reads: the only way evidence reaches a model.

Distilled from google-research/harness2 `core.context`.

    context/task.md              the task as the agent received it
    context/source/              task source material (answer-key globs removed)
    context/rollouts/<label>.md  FULL trajectories -- never clipped to fit a prompt
    context/deliverables/<label>.md
    context/harness/<rel>        the editable tree being refined
    context/library/INDEX.md     earlier tasks in this domain, with their full harnesses
    context/pool/<label>/        candidate harness + diff + rollout (compose stages only)
    context/decisions/<label>.md earlier edit / composition decisions
    MISSION.md                   what to do with all of it

Evidence is served as files and the prompt is a short pointer, so nothing is truncated to fit.
The finished tree must pass both tripwires before a model can see it.
"""

from __future__ import annotations

import difflib
import fnmatch
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import structlog

from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.evidence_model import (
    EvidenceTree,
    PoolItem,
    mission,
)
from harness.services.recursive_harnessing.guards import (
    assert_no_leak_paths,
    assert_no_verdicts,
    iter_files,
)
from harness.services.recursive_harnessing.models import RunView
from harness.services.recursive_harnessing.protocols import TaskAdapter

__all__ = [
    "EvidenceTree",
    "PoolItem",
    "build_evidence",
    "mission",
]

logger = structlog.get_logger(__name__)


def _copy_source(adapter: TaskAdapter, task_id: str, root: Path) -> int:
    src = adapter.task_files(task_id)
    if not src or not Path(src).is_dir():
        return 0
    globs = [g.lstrip("./") for g in adapter.leak_globs]
    n = 0
    for f in iter_files(src):
        rel = f.relative_to(src).as_posix()
        if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, f"*/{g}") for g in globs):
            continue
        target = root / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        n += 1
    return n


def _write_rollout(dest: Path, rv: RunView, adapter: TaskAdapter) -> str:
    """Write one rollout's trajectory and deliverable; return "" or the failure detail."""
    failure = ""
    try:
        traj = adapter.trajectory(rv.run_dir)
    except Exception as exc:  # the failure is itself evidence
        traj, failure = f"(trajectory unavailable: {type(exc).__name__}: {exc})", f"{rv.label}: {exc}"
    (dest / "rollouts" / f"{rv.label}.md").write_text(traj, encoding="utf-8")
    try:
        text = adapter.deliverable_text(rv.run_dir) or "(no deliverable produced)"
    except Exception as exc:
        text = f"(deliverable unavailable: {type(exc).__name__}: {exc})"
    (dest / "deliverables" / f"{rv.label}.md").write_text(text, encoding="utf-8")
    return failure


def _write_pool(dest: Path, pool: Sequence[PoolItem], adapter: TaskAdapter) -> list[str]:
    spec, got = adapter.surface, []
    reference = S.read_tree(spec, dest / "harness")
    for label, cand_dir, rv in pool:
        d = dest / "pool" / label
        d.mkdir(parents=True, exist_ok=True)
        if cand_dir and Path(cand_dir).is_dir():
            assert_no_leak_paths(cand_dir, adapter.leak_globs)
            cand = S.read_tree(spec, cand_dir)
            S.write_tree(spec, cand, d / "harness")
            diff = "".join(
                line
                for name in sorted(reference.keys() | cand.keys())
                for line in difflib.unified_diff(
                    reference.get(name, "").splitlines(keepends=True),
                    cand.get(name, "").splitlines(keepends=True),
                    fromfile=f"current/{name}",
                    tofile=f"{label}/{name}",
                )
            )
            (d / "harness.diff").write_text(diff, encoding="utf-8")
        if rv is not None:
            try:
                (d / "rollout.md").write_text(adapter.trajectory(rv.run_dir), encoding="utf-8")
                (d / "produced.md").write_text(
                    adapter.deliverable_text(rv.run_dir) or "(nothing produced)", encoding="utf-8"
                )
            except Exception as exc:
                (d / "rollout.md").write_text(f"(unavailable: {exc})", encoding="utf-8")
        got.append(label)
    return got


def build_evidence(
    dest: Path | str,
    adapter: TaskAdapter,
    task_id: str,
    rollouts: Sequence[RunView] = (),
    *,
    harness_dir: Path | None = None,
    library_dir: Path | None = None,
    pool: Sequence[PoolItem] = (),
    decisions: Mapping[str, str] | None = None,
) -> EvidenceTree:
    """Write the evidence tree and return what landed, so the mission describes only that.

    Runs inside the stage failure domain: an adapter or leak error raised here is recorded as
    a stage error. Only trajectory/deliverable *readers* are caught, because their failure is
    itself evidence.
    """
    root = Path(dest)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    (root / "task.md").write_text(adapter.task_prompt(task_id), encoding="utf-8")
    source_files = _copy_source(adapter, task_id, root)
    for label, notes in (decisions or {}).items():
        (root / "decisions").mkdir(exist_ok=True)
        (root / "decisions" / f"{label}.md").write_text(notes or "No decision notes returned.", encoding="utf-8")
    failed: list[str] = []
    got: list[str] = []
    if rollouts:
        (root / "rollouts").mkdir()
        (root / "deliverables").mkdir()
    for rv in rollouts:
        failure = _write_rollout(root, rv, adapter)
        (failed if failure else got).append(failure or rv.label)
    n_h = 0
    if harness_dir and Path(harness_dir).is_dir():
        assert_no_leak_paths(harness_dir, adapter.leak_globs)
        tree = S.read_tree(adapter.surface, harness_dir)
        S.write_tree(adapter.surface, tree, root / "harness")
        n_h = len(tree)
    pooled = _write_pool(root, pool, adapter)
    lib = False
    if library_dir and Path(library_dir).is_dir() and any(Path(library_dir).iterdir()):
        assert_no_leak_paths(library_dir, adapter.leak_globs)
        shutil.copytree(library_dir, root / "library", dirs_exist_ok=True)
        lib = True
    assert_no_leak_paths(root, adapter.leak_globs)
    assert_no_verdicts(root)
    if rollouts and not got:
        raise RuntimeError(
            "no trajectory could be rendered for ANY rollout -- the proposer would be "
            "adapting on nothing: " + "; ".join(failed[:4])
        )
    return EvidenceTree(
        root=root,
        rollouts=tuple(got),
        harness_files=n_h,
        library=lib,
        pool=tuple(pooled),
        source_files=source_files,
        decisions=len(decisions or {}),
        failed=tuple(failed),
    )
