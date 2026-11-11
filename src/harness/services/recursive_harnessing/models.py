"""Slotted/frozen domain models for recursive harnessing (Rules 12, 43).

Distilled from google/harness2 (arXiv 2610.14224, Apache-2.0): a *harness* is an editable
component tree (always-on guidance, skills, scripts, sub-agents); *recursion* proposes,
probes and composes edits to that tree while model weights stay fixed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Tree = dict[str, str]
"""A harness: relative path -> file text. Omitted paths are inherited, never deleted."""


@dataclass(slots=True, frozen=True)
class SurfaceSpec:
    """The editable surface of one agent framework: paths, caps and per-surface rules."""

    name: str
    always_on: tuple[str, ...]
    always_on_max: int
    skill_dir: str
    trigger_line: str = "- When {desc}, use the `{name}` skill."
    subagent_dir: str = "sub_agents"
    allow_subagents: bool = False
    reserved_scripts: frozenset[str] = frozenset()
    description_bounds: tuple[int, int] | None = None
    scripts_dir: str = "scripts"
    require_always_on_triggers: bool = True

    def __post_init__(self) -> None:
        if not self.always_on:
            raise ValueError("SurfaceSpec.always_on needs at least one file")
        if self.always_on_max <= 0:
            raise ValueError("SurfaceSpec.always_on_max must be positive")
        if "{name}" not in self.trigger_line:
            raise ValueError("SurfaceSpec.trigger_line must contain a {name} placeholder")
        if self.description_bounds and self.description_bounds[0] > self.description_bounds[1]:
            raise ValueError("SurfaceSpec.description_bounds must be (min, max) with min <= max")


BRAIN_SURFACE = SurfaceSpec(
    name="brain",
    always_on=("AGENTS.md",),
    always_on_max=32_000,
    skill_dir=".agents/skills",
    description_bounds=(100, 350),  # Rule 44 Tier-1 catalog budget
    require_always_on_triggers=False,
)


@dataclass(slots=True, frozen=True)
class RunView:
    """What the method knows about one finished rollout. Never carries a score."""

    label: str
    run_id: str
    run_dir: Path
    ok: bool
    delivered: bool
    cost_usd: float = 0.0
    error: str = ""


@dataclass(slots=True, frozen=True)
class ProposalReply:
    """One proposer session: its text, the edited harness directory, and what it cost."""

    text: str
    workspace: Path | None = None
    cost_usd: float = 0.0
    attempts: int = 1
    cached: bool = False


@dataclass(slots=True, frozen=True)
class SelectorChoice:
    """A selector's pick among anonymous candidate ids."""

    anon_id: str
    why: str = ""
    cost_usd: float = 0.0


@dataclass(slots=True, frozen=True)
class Stage:
    """An improvement stage, including retries, its harness, and decision notes."""

    label: str
    dim: str
    tree: Tree
    kept_base: bool = False
    fell_back: bool = False
    error: str = ""
    usd: float = 0.0
    attempts: int = 0
    cached: bool = False
    notes: str = ""
    execution_failed: bool = False


@dataclass(slots=True)
class ModeResult:
    """Everything one recursion mode produced for one task (accumulated during the run)."""

    mode: str
    task_id: str
    k: int
    stages: list[Stage] = field(default_factory=list)
    trees: dict[str, Tree] = field(default_factory=dict)
    rollouts: dict[str, RunView] = field(default_factory=dict)
    finals: list[str] = field(default_factory=list)
    ledger: Any = None  # BudgetLedger (typed Any to keep models import-cycle free)
    similarity: dict | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.finals) and not self.errors and not any(s.execution_failed for s in self.stages)

    @property
    def fell_back(self) -> list[str]:
        return [s.label for s in self.stages if s.fell_back]

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "task_id": self.task_id,
            "k": self.k,
            "finals": self.finals,
            "ok": self.ok,
            "fell_back": self.fell_back,
            "kept_base": [s.label for s in self.stages if s.kept_base],
            "stages": [
                {
                    "label": s.label,
                    "dim": s.dim,
                    "fell_back": s.fell_back,
                    "kept_base": s.kept_base,
                    "execution_failed": s.execution_failed,
                    "attempts": s.attempts,
                    "usd": s.usd,
                    "cached": s.cached,
                    "notes": s.notes,
                    "error": s.error[:400],
                }
                for s in self.stages
            ],
            "similarity": self.similarity,
            "ledger": self.ledger.to_dict() if self.ledger else None,
            "errors": self.errors,
        }


@dataclass(slots=True, frozen=True)
class Selection:
    """The outcome of blind selection over anonymised candidate artifacts."""

    task_id: str
    mode: str
    k: int
    chosen_id: str = ""
    chosen_label: str = ""
    chosen_run_id: str = ""
    chosen_is_base: bool = False
    why: str = ""
    id_map: dict[str, str] = field(default_factory=dict)
    dropped: tuple[str, ...] = ()
    n_candidates: int = 0
    ok: bool = False
    fallback: bool = False
    error: str = ""
    usd: float = 0.0
    trivial: bool = False
