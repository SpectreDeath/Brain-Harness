"""Slotted and frozen domain dataclasses for conversation trajectory mining (Rule 12, Rule 43)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class TrajectoryStepRecord:
    """Slotted and frozen execution step record (Rule 12)."""

    idx: int
    step_type: str
    status: str
    has_subtrajectory: bool = False
    task_details: str = ""
    error_details: str = ""
    byte_offset: int = 0
    byte_length: int = 0

    def __post_init__(self) -> None:
        if self.idx < 0:
            raise ValueError(f"Step index cannot be negative, got {self.idx}")


@dataclass(slots=True, frozen=True)
class FailureCluster:
    """Slotted and frozen aggregated failure mode cluster (Rule 12)."""

    error_type: str
    count: int
    sample_cids: tuple[str, ...]
    tool_names: tuple[str, ...]
    sample_messages: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError(f"Failure count cannot be negative, got {self.count}")


@dataclass(slots=True, frozen=True)
class ConversationManifest:
    """Slotted and frozen manifest summary for a single conversation database (Rule 12)."""

    cid: str
    db_path: str
    file_size_bytes: int
    step_count: int
    has_wal: bool
    step_types: dict[str, int]
    errors_detected: int = 0
    first_prompt_snippet: str = ""
    retry_count: int = 0

    def __post_init__(self) -> None:
        if self.file_size_bytes < 0:
            raise ValueError(f"File size cannot be negative: {self.file_size_bytes}")
        if self.step_count < 0:
            raise ValueError(f"Step count cannot be negative: {self.step_count}")


@dataclass(slots=True, frozen=True)
class FrictionScorecard:
    """Slotted and frozen aggregate friction scorecard across session histories (Rule 12)."""

    total_conversations: int
    total_steps: int
    total_bytes_mb: float
    total_errors: int
    error_rate: float
    step_type_distribution: dict[str, int]
    high_friction_sessions: tuple[dict[str, Any], ...]
    failure_clusters: tuple[FailureCluster, ...]

    def __post_init__(self) -> None:
        if self.total_conversations < 0:
            raise ValueError(f"total_conversations cannot be negative: {self.total_conversations}")


@dataclass(slots=True, frozen=True)
class IsnadClaimRecord:
    """Slotted and frozen epistemic claim with unbroken isnad provenance (Rule 12, Rule 41)."""

    claim_id: str
    assertion: str
    isnad_source: str
    test_anchor: str
    confidence: float = 1.0


@dataclass(slots=True, frozen=True)
class CognitiveBifurcationReport:
    """Slotted and frozen dual-lens distillation output report (Rule 12, Rule 41)."""

    cid: str
    knowledge_vault_path: str
    skill_scaffold_path: str
    extracted_invariants: tuple[str, ...]
    procedural_rules: tuple[str, ...]


__all__ = [
    "CognitiveBifurcationReport",
    "ConversationManifest",
    "FailureCluster",
    "FrictionScorecard",
    "IsnadClaimRecord",
    "TrajectoryStepRecord",
]
