"""Default service implementations: thin facades over the deterministic domain engine (Rule 49)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from harness.services.recursive_harnessing import guards, identity
from harness.services.recursive_harnessing import surface as S
from harness.services.recursive_harnessing.ledger import BudgetLedger
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import ModeResult, RunView, SurfaceSpec, Tree
from harness.services.recursive_harnessing.protocols import CandidateSelector, HarnessProposer, TaskAdapter
from harness.services.recursive_harnessing.recursion import run_mode
from harness.services.recursive_harnessing.selection import blind_select


class DefaultEvidenceIsolationService:
    """Tripwires + trial identity, resolved through `service.evidence_isolation`."""

    def assert_no_leak_paths(self, root: Path | str, patterns: Sequence[str]) -> None:
        guards.assert_no_leak_paths(root, patterns)

    def assert_no_verdicts(self, root: Path | str) -> None:
        guards.assert_no_verdicts(root)

    def assert_tree_clean(self, tree: Mapping[str, str]) -> None:
        guards.assert_tree_clean(tree)

    def scrub_env(self, base_env: Mapping[str, str] | None = None, *, keep: Sequence[str] = ()) -> dict[str, str]:
        return guards.scrub_env(base_env, keep=keep)

    def fingerprint_dir(self, harness_dir: Path | str | None) -> str:
        return identity.fingerprint_dir(harness_dir)

    def fingerprint_tree(self, tree: Mapping[str, str]) -> str:
        return identity.fingerprint_tree(tree)

    def mark_complete(
        self, where: Path | str, *, run_id: str, harness_dir: Path | str | None = None, inputs: str | None = None
    ) -> Path:
        return identity.mark_complete(where, run_id=run_id, harness_dir=harness_dir, inputs=inputs)

    def is_complete(
        self,
        where: Path | str,
        *,
        harness_dir: Path | str | None = None,
        match_harness: bool = True,
        inputs: str | None = None,
    ) -> bool:
        return identity.is_complete(where, harness_dir=harness_dir, match_harness=match_harness, inputs=inputs)


class DefaultRecursiveRefinerService:
    """Propose-Probe-Compose recursion, blind selection and experience, via `service.recursive_refiner`."""

    def validate_harness(self, spec: SurfaceSpec, tree: Tree) -> dict:
        return S.validate(spec, tree)

    def new_ledger(self, mode: str, task_id: str, k: int) -> BudgetLedger:
        return BudgetLedger(mode=mode, task_id=task_id, k=k)

    def open_library(self, root: Path | str, domain: str, spec: SurfaceSpec) -> ExperienceLibrary:
        return ExperienceLibrary(Path(root), domain, spec)

    def refine(
        self,
        mode: str,
        task_id: str,
        k: int,
        base: Sequence[RunView],
        *,
        adapter: TaskAdapter,
        proposer: HarnessProposer,
        work_dir: Path | str,
        run_id_of: Callable[[str], str],
        base_tree: Tree,
        library_dir: Path | None = None,
    ) -> ModeResult:
        return run_mode(
            mode,
            task_id,
            k,
            base,
            adapter=adapter,
            proposer=proposer,
            work_dir=work_dir,
            run_id_of=run_id_of,
            base_tree=base_tree,
            library_dir=library_dir,
        )

    def select(
        self,
        task_id: str,
        k: int,
        mode: str,
        candidates: dict[str, RunView],
        *,
        adapter: TaskAdapter,
        selector: CandidateSelector,
        work_dir: Path | str,
    ) -> Any:
        return blind_select(task_id, k, mode, candidates, adapter=adapter, selector=selector, work_dir=work_dir)
