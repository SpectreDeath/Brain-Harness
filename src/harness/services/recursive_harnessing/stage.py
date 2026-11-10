"""One improvement stage: build evidence, propose an edit, retry an invalid proposal once.

Distilled from google/harness2 `core.recursion._run_stage`. Failure semantics are the point:

* evidence that cannot be built (including a tripwire) -> the stage *inherits the fallback*;
* a proposal that fails validation gets the validator's prose back as retry feedback, once;
* a dead proposer channel is flagged `execution_failed` (an infrastructure fault, not a verdict);
* after the last attempt the stage inherits the fallback harness -- it never raises.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import structlog

from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.evidence import PoolItem, build_evidence, mission
from harness.services.recursive_harnessing.errors import ProposerError
from harness.services.recursive_harnessing.guards import assert_tree_clean
from harness.services.recursive_harnessing.models import RunView, Stage, Tree
from harness.services.recursive_harnessing.protocols import HarnessProposer, TaskAdapter

logger = structlog.get_logger(__name__)
STAGE_ATTEMPTS = 2
_NOTES = re.compile(r"<notes>(.*?)</notes>", re.S)


def accept_tree(adapter: TaskAdapter, new: Tree, fallback: Tree) -> tuple[bool, str]:
    """Repair then validate a proposed tree: (kept_base, "") if accepted, else (kept_base, error)."""
    spec = adapter.surface
    repaired = S.autotrigger(spec, new)
    if repaired:
        logger.debug("autotriggered_skills", skills=repaired)
    d = S.diff_summary(spec, fallback, new)
    kept = not (d["added"] or d["removed"] or d["modified"])
    try:
        S.validate(spec, new)
        adapter.validate_tree(new)
        assert_tree_clean(new)
    except ValueError as exc:
        return kept, str(exc)
    return kept, ""


def _fell_back(
    label: str,
    dim: str,
    fallback: Tree,
    err: str,
    *,
    usd: float = 0.0,
    attempts: int = 0,
    cached: bool = False,
    failed: bool = False,
) -> Stage:
    return Stage(
        label=label,
        dim=dim,
        tree=dict(fallback),
        fell_back=True,
        error=err[:400],
        usd=usd,
        attempts=attempts,
        cached=cached,
        execution_failed=failed,
    )


def _feedback(err: str) -> str:
    return (
        (f"\n\n# YOUR PREVIOUS ATTEMPT WAS REJECTED\n\n{err}\n\nFix it in `context/harness/` and reply again.")
        if err
        else ""
    )


def run_stage(
    *,
    label: str,
    dim: str,
    job: str,
    fallback: Tree,
    adapter: TaskAdapter,
    proposer: HarnessProposer,
    ctx_dir: Path | str,
    task_id: str,
    rollouts: Sequence[RunView],
    harness_dir: Path | None,
    library_dir: Path | None = None,
    pool: Sequence[PoolItem] = (),
    decisions: Mapping[str, str] | None = None,
    max_attempts: int = STAGE_ATTEMPTS,
) -> Stage:
    """Build evidence, propose an edit, and retry an invalid proposal; never raises."""
    spec = adapter.surface
    try:
        ev = build_evidence(
            Path(ctx_dir) / label,
            adapter,
            task_id,
            rollouts,
            harness_dir=harness_dir,
            library_dir=library_dir,
            pool=pool,
            decisions=decisions,
        )
        text = mission(ev, job=job)
        (ev.root / "MISSION.md").write_text(text, encoding="utf-8")
    except Exception as exc:  # stage failure domain: record, inherit fallback, keep going
        logger.warning("evidence_build_failed", label=label, error=str(exc))
        return _fell_back(label, dim, fallback, f"could not build evidence: {type(exc).__name__}: {exc}")

    err, usd, calls, cached, failed = "", 0.0, 0, True, False
    for attempt in range(1, max_attempts + 1):
        try:
            reply = proposer.propose(text + _feedback(err), ev.root, f"{label}.a{attempt}")
        except ProposerError as exc:
            err, failed, cached = str(exc), True, False
            calls += exc.attempts or 1
            usd += exc.cost_usd
            break
        usd += reply.cost_usd
        calls += 0 if reply.cached else max(1, reply.attempts)
        cached = cached and reply.cached
        if reply.workspace is None:
            err = "the harness directory did not come back; edit the files in `context/harness/` in place"
            continue
        rejected: list[str] = []
        new = S.read_tree(spec, reply.workspace, rejected=rejected)
        if not new:
            err = "`context/harness/` came back empty -- edit the files, do not delete them all"
            continue
        if rejected:
            err = (
                "these files are off the editable surface and were not applied: "
                + ", ".join(sorted(rejected)[:6])
                + f". Skills live at `{spec.skill_dir}/<name>/SKILL.md`, "
                f"scripts at `{spec.scripts_dir}/<name>.py`; names are lowercase letters, digits, `_`, `-`."
            )
            S.write_tree(spec, new, ev.root / "harness")
            continue
        kept, err = accept_tree(adapter, new, fallback)
        if err:
            S.write_tree(spec, new, ev.root / "harness")
            continue
        notes = _NOTES.search(reply.text)
        return Stage(
            label=label,
            dim=dim,
            tree=new,
            kept_base=kept,
            usd=usd,
            attempts=calls,
            cached=cached,
            notes=(notes.group(1) if notes else reply.text).strip(),
        )
    return _fell_back(label, dim, fallback, err, usd=usd, attempts=calls, cached=cached, failed=failed)
