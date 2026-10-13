"""Slotted and frozen verification check models for Codebase Context (Rule 12 & Rule 43)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(slots=True, frozen=True)
class TokenBudgetCheck:
    """Evaluation result for an always-loaded context file token budget."""

    file_path: str
    token_count: int
    token_ceiling: int
    passed: bool
    message: str

    def __post_init__(self) -> None:
        assert self.file_path, "file_path cannot be empty"
        assert self.token_ceiling >= 0, "token_ceiling must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "token_budget",
            "file": self.file_path,
            "tokens": self.token_count,
            "ceiling": self.token_ceiling,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class PathIntegrityCheck:
    """Evaluation result verifying that an inline backtick path exists on disk."""

    file_path: str
    target_path: str
    resolved_path: str
    passed: bool
    message: str

    def __post_init__(self) -> None:
        assert self.file_path, "file_path cannot be empty"
        assert self.target_path, "target_path cannot be empty"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "path_existence",
            "file": self.file_path,
            "target_path": self.target_path,
            "resolved_path": self.resolved_path,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class ScriptIntegrityCheck:
    """Evaluation result verifying that a mentioned command exists in project manifests."""

    file_path: str
    raw_command: str
    runner: str
    script_name: str
    passed: bool
    message: str

    def __post_init__(self) -> None:
        assert self.file_path, "file_path cannot be empty"
        assert self.script_name, "script_name cannot be empty"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "script_existence",
            "file": self.file_path,
            "script": self.raw_command,
            "runner": self.runner,
            "script_name": self.script_name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class SyncDriftCheck:
    """Evaluation result verifying that generated vendor files match canonical source."""

    target_file: str
    canonical_source: str
    passed: bool
    message: str

    def __post_init__(self) -> None:
        assert self.target_file, "target_file cannot be empty"
        assert self.canonical_source, "canonical_source cannot be empty"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "sync_drift",
            "file": self.target_file,
            "canonical_source": self.canonical_source,
            "passed": self.passed,
            "message": self.message,
        }


CheckResult = Union[TokenBudgetCheck, PathIntegrityCheck, ScriptIntegrityCheck, SyncDriftCheck]


@dataclass(slots=True, frozen=True)
class ContextLintReport:
    """Authoritative, immutable verification report for repository context files."""

    root_path: str
    passed: bool
    checks: tuple[CheckResult, ...] = field(default_factory=tuple)
    problems_count: int = 0
    checks_count: int = 0

    @property
    def problems(self) -> tuple[CheckResult, ...]:
        """Return only checks that failed."""
        return tuple(c for c in self.checks if not c.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root_path,
            "passed": self.passed,
            "problems_count": self.problems_count,
            "checks_count": self.checks_count,
            "problems": [p.to_dict() for p in self.problems],
            "all_checks": [c.to_dict() for c in self.checks],
        }


@dataclass(slots=True, frozen=True)
class SyncResult:
    """Result of synchronizing multi-format context files from canonical source."""

    root_path: str
    in_sync: bool
    actions: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root_path,
            "in_sync": self.in_sync,
            "actions": list(self.actions),
        }
