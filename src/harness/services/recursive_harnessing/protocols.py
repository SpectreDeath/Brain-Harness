"""Protocols for recursive harnessing (Rules 2, 49).

The method knows three outside things -- the *task adapter* (how a rollout runs and is read),
the *proposer* (an agentic session that edits a harness directory) and the *selector* (a blind
chooser). Everything else is deterministic and lives in this package.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.services.recursive_harnessing.models import (
    ModeResult,
    ProposalReply,
    RunView,
    SelectorChoice,
    SurfaceSpec,
    Tree,
)


@runtime_checkable
class TaskAdapter(Protocol):
    """Implement these and the whole method works. Nothing here is method logic."""

    surface: SurfaceSpec
    leak_globs: tuple[str, ...]
    work: str  # what the practitioner needs -- never how it is measured
    deliverable: str  # the noun for the produced artifact ("report", "workbook", ...)

    def task_prompt(self, task_id: str) -> str:
        """The task as the agent received it, with criteria and expected output stripped."""

    def task_files(self, task_id: str) -> Path | None:
        """Optional source material the work was done against, or None."""

    def execute(self, task_id: str, harness_dir: Path | None, run_id: str) -> Path:
        """Run one rollout and return its run directory (idempotent by run_id).

        `harness_dir=None` means the unmodified base harness.
        """

    def delivered(self, run_dir: Path) -> bool:
        """Did this rollout produce the artifact the task asked for?"""

    def trajectory(self, run_dir: Path) -> str:
        """Readable trajectory of the rollout, complete (never clipped to fit a prompt)."""

    def deliverable_text(self, run_dir: Path) -> str:
        """The artifact as text, extracted from agent-authored bytes only."""

    def validate_tree(self, tree: Tree) -> None:
        """Task-specific harness invariants; raise ValueError listing all problems as prose."""


@runtime_checkable
class HarnessProposer(Protocol):
    """An agentic session that edits `<evidence_root>/harness` in place and replies with notes."""

    def propose(self, mission: str, evidence_root: Path, label: str) -> ProposalReply:
        """Raise `ProposerError` when no usable reply exists."""


@runtime_checkable
class CandidateSelector(Protocol):
    """A blind chooser over anonymous artifact texts keyed by arbitrary ids."""

    def choose(self, task_text: str, candidates: Mapping[str, str]) -> SelectorChoice:
        """Raise `SelectorError` (or ValueError) on failure; the caller degrades neutrally."""


@runtime_checkable
class EvidenceIsolationService(Protocol):
    """Fail-closed tripwires and trial identity for evidence that will reach a model."""

    def assert_no_leak_paths(self, root: Path | str, patterns: Sequence[str]) -> None: ...

    def assert_no_verdicts(self, root: Path | str) -> None: ...

    def assert_tree_clean(self, tree: Mapping[str, str]) -> None: ...

    def scrub_env(self, base_env: Mapping[str, str] | None = None, *, keep: Sequence[str] = ()) -> dict[str, str]: ...

    def fingerprint_dir(self, harness_dir: Path | str | None) -> str: ...

    def fingerprint_tree(self, tree: Mapping[str, str]) -> str: ...

    def mark_complete(
        self, where: Path | str, *, run_id: str, harness_dir: Path | str | None = None, inputs: str | None = None
    ) -> Path: ...

    def is_complete(
        self,
        where: Path | str,
        *,
        harness_dir: Path | str | None = None,
        match_harness: bool = True,
        inputs: str | None = None,
    ) -> bool: ...


@runtime_checkable
class RecursiveRefinerService(Protocol):
    """Propose-Probe-Compose task-level recursion plus per-domain experience."""

    def validate_harness(self, spec: SurfaceSpec, tree: Tree) -> dict: ...

    def new_ledger(self, mode: str, task_id: str, k: int) -> Any: ...

    def open_library(self, root: Path | str, domain: str, spec: SurfaceSpec) -> Any: ...

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
    ) -> ModeResult: ...

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
    ) -> Any: ...
