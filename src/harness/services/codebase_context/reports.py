"""Slotted and frozen governance and smell violation models for Codebase Context (Rule 12 & Rule 43)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class ContextSmellViolation:
    """Immutable record of an instruction or context file defect (Rule 12)."""

    rule_name: str
    file_path: str
    line_number: int
    message: str
    severity: str = "ERROR"

    def __post_init__(self) -> None:
        assert self.rule_name, "rule_name cannot be empty"
        assert self.file_path, "file_path cannot be empty"
        assert self.severity in ("WARNING", "ERROR", "CRITICAL"), f"Invalid severity: {self.severity}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule_name,
            "file": self.file_path,
            "line": self.line_number,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(slots=True, frozen=True)
class GovernanceStageResult:
    """Immutable result of a single context governance stage (Rule 12)."""

    stage_num: int
    stage_name: str
    passed: bool
    duration_ms: float
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert 1 <= self.stage_num <= 5, f"Invalid stage number: {self.stage_num}"
        assert self.stage_name, "stage_name cannot be empty"

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_num": self.stage_num,
            "stage_name": self.stage_name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(slots=True, frozen=True)
class ContextGovernanceReport:
    """Immutable report aggregating complete context governance cycle (Rule 12)."""

    workspace_root: str
    passed: bool
    recommended_tier: str
    stages: tuple[GovernanceStageResult, ...] = field(default_factory=tuple)
    violations: tuple[ContextSmellViolation, ...] = field(default_factory=tuple)

    @property
    def total_stages(self) -> int:
        return len(self.stages)

    @property
    def passed_stages_count(self) -> int:
        return sum(1 for s in self.stages if s.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_root": self.workspace_root,
            "passed": self.passed,
            "recommended_tier": self.recommended_tier,
            "total_stages": self.total_stages,
            "passed_stages_count": self.passed_stages_count,
            "stages": [s.to_dict() for s in self.stages],
            "violations": [v.to_dict() for v in self.violations],
        }
