"""Slotted domain models, keys, and budget constants for Harness Spawner."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import (
    BRAIN_SURFACE,
    SurfaceSpec,
)

from .constants import (
    DEFAULT_K,
    DEFAULT_MAX_ROLLOUTS,
    DEFAULT_MAX_SESSIONS,
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    EXPERIENCE_LIBRARY_KEY,
    HARD_MAX_SPAWN_DEPTH,
    SPAWN_DEPTH_KEY,
    SPAWN_MAX_DEPTH_KEY,
)


class SpawnLifecycleState(str, Enum):
    """Lifecycle states of a spawned child harness."""

    SPAWNED = "SPAWNED"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


@dataclass(slots=True, frozen=True)
class SpawnBudgetSpec:
    """Dual resource budget bounding tokens and rollout/session counts (Rules 12, 43)."""

    max_tokens: int = DEFAULT_MAX_TOKENS
    k: int = DEFAULT_K
    max_rollouts: int = DEFAULT_MAX_ROLLOUTS
    max_sessions: int = DEFAULT_MAX_SESSIONS

    def __post_init__(self) -> None:
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
        if self.k < 1:
            raise ValueError(f"k must be >= 1, got {self.k}")
        if self.max_rollouts < 1:
            raise ValueError(f"max_rollouts must be >= 1, got {self.max_rollouts}")
        if self.max_sessions < 1:
            raise ValueError(f"max_sessions must be >= 1, got {self.max_sessions}")


@dataclass(slots=True, frozen=True)
class SpawnSpec:
    """Typed declaration of a child harness to validate, probe, and run (Rules 12, 43)."""

    name: str
    domain: str
    task: str = "spawned_harness"
    surface: SurfaceSpec = field(default_factory=lambda: BRAIN_SURFACE)
    tree: dict[str, str] = field(default_factory=dict)
    isolated_keys: tuple[str, ...] = ("service.experience_library",)
    budget: SpawnBudgetSpec = field(default_factory=SpawnBudgetSpec)
    save_dir: Path = field(default_factory=lambda: Path(".harness/spawns"))
    parent_session_id: str | None = None
    parent_spawn_id: str | None = None
    current_depth: int = 0
    max_spawn_depth: int = DEFAULT_MAX_SPAWN_DEPTH
    lifetime: str = "persistent"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("SpawnSpec.name must be non-empty")
        if not self.domain or not self.domain.strip():
            raise ValueError("SpawnSpec.domain must be non-empty")
        if self.current_depth < 0:
            raise ValueError(f"SpawnSpec.current_depth must be >= 0, got {self.current_depth}")
        if self.max_spawn_depth < 1 or self.max_spawn_depth > HARD_MAX_SPAWN_DEPTH:
            raise ValueError(f"SpawnSpec.max_spawn_depth={self.max_spawn_depth} must be in [1, {HARD_MAX_SPAWN_DEPTH}]")
        if self.lifetime not in ("task", "persistent"):
            raise ValueError(f"SpawnSpec.lifetime must be 'task' or 'persistent', got {self.lifetime!r}")
        if not isinstance(self.save_dir, Path):
            object.__setattr__(self, "save_dir", Path(self.save_dir))


@dataclass(slots=True, frozen=True)
class SpawnTrialResult:
    """Outcome of the admission validation + k=1 deterministic probe gate."""

    passed: bool
    fingerprint: str
    census: dict[str, int]
    probe_tokens_used: int = 0
    errors: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class SpawnMergeProposal:
    """Staged child learning awaiting explicit parent review and adoption."""

    proposal_id: str
    spawn_id: str
    domain: str
    task_id: str
    tree: dict[str, str]
    cue: str
    lesson: str
    evidence: str
    why: str = ""
    ki_id: str = ""
    status: str = "pending"

    def __post_init__(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("SpawnMergeProposal.proposal_id must be non-empty")
        if not self.spawn_id.strip():
            raise ValueError("SpawnMergeProposal.spawn_id must be non-empty")
        if not self.domain.strip():
            raise ValueError("SpawnMergeProposal.domain must be non-empty")
        if not self.task_id.strip():
            raise ValueError("SpawnMergeProposal.task_id must be non-empty")
        for field_name in ("cue", "lesson", "evidence"):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"SpawnMergeProposal.{field_name} must be non-empty")
        if self.status not in ("pending", "adopted", "rejected"):
            raise ValueError(f"Invalid proposal status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "spawn_id": self.spawn_id,
            "domain": self.domain,
            "task_id": self.task_id,
            "tree": dict(self.tree),
            "cue": self.cue,
            "lesson": self.lesson,
            "evidence": self.evidence,
            "why": self.why,
            "ki_id": self.ki_id,
            "status": self.status,
        }


@dataclass(slots=True, frozen=True)
class SpawnedHarnessRecord:
    """Immutable snapshot of a spawned child harness and its resource consumption."""

    spawn_id: str
    name: str
    domain: str
    task: str
    state: SpawnLifecycleState
    depth: int
    max_spawn_depth: int
    parent_spawn_id: str | None
    parent_session_id: str | None
    session_id: str
    node_id: str
    fingerprint: str
    save_dir: str
    tokens_used: int
    rollouts_used: int
    sessions_used: int
    budget: SpawnBudgetSpec
    lifetime: str
    trial: SpawnTrialResult | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        trial_dict: dict[str, Any] | None = None
        if self.trial is not None:
            trial_dict = {
                "passed": self.trial.passed,
                "fingerprint": self.trial.fingerprint,
                "census": dict(self.trial.census),
                "probe_tokens_used": self.trial.probe_tokens_used,
                "errors": list(self.trial.errors),
            }
        return {
            "spawn_id": self.spawn_id,
            "name": self.name,
            "domain": self.domain,
            "task": self.task,
            "state": self.state.value,
            "depth": self.depth,
            "max_spawn_depth": self.max_spawn_depth,
            "parent_spawn_id": self.parent_spawn_id,
            "parent_session_id": self.parent_session_id,
            "session_id": self.session_id,
            "node_id": self.node_id,
            "fingerprint": self.fingerprint,
            "save_dir": self.save_dir,
            "tokens_used": self.tokens_used,
            "rollouts_used": self.rollouts_used,
            "sessions_used": self.sessions_used,
            "budget": {
                "max_tokens": self.budget.max_tokens,
                "k": self.budget.k,
                "max_rollouts": self.budget.max_rollouts,
                "max_sessions": self.budget.max_sessions,
            },
            "lifetime": self.lifetime,
            "trial": trial_dict,
            "error": self.error,
        }


@dataclass(slots=True)
class _RuntimeHandle:
    """Mutable runtime handle for live child contexts and libraries."""

    contexts: tuple[ServiceContext, ...]
    library: ExperienceLibrary
    surface: SurfaceSpec
    tree: dict[str, str]
    disposed: bool = False


__all__ = [
    "HARD_MAX_SPAWN_DEPTH",
    "DEFAULT_MAX_SPAWN_DEPTH",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_K",
    "DEFAULT_MAX_ROLLOUTS",
    "DEFAULT_MAX_SESSIONS",
    "SpawnLifecycleState",
    "EXPERIENCE_LIBRARY_KEY",
    "SPAWN_DEPTH_KEY",
    "SPAWN_MAX_DEPTH_KEY",
    "SpawnBudgetSpec",
    "SpawnSpec",
    "SpawnTrialResult",
    "SpawnMergeProposal",
    "SpawnedHarnessRecord",
    "_RuntimeHandle",
]
