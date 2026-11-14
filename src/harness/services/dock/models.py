"""Slotted domain models and exceptions for Repository Dock service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class DockPermissions:
    """Capability permissions declared in dock manifest (Rule 12)."""

    read: bool = True
    run: bool = True
    write: bool = False
    push: bool = False


@dataclass(slots=True, frozen=True)
class DockBoundaries:
    """Path and operation boundaries that cannot be crossed (Rule 12)."""

    paths: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class DockStep:
    """Individual sequential execution step within a procedure (Rule 12)."""

    command: str = ""
    workdir: str = "."
    expected_output: str = ""
    call_procedure: str | None = None

    def __post_init__(self) -> None:
        has_cmd = bool(self.command and self.command.strip())
        has_call = bool(self.call_procedure and self.call_procedure.strip())
        if has_cmd == has_call:
            raise ValueError("DockStep must define exactly one of 'command' or 'call_procedure'")


@dataclass(slots=True, frozen=True)
class DockProcedure:
    """Named executable procedure containing sequential steps (Rule 12)."""

    name: str
    description: str = ""
    steps: tuple[DockStep, ...] = ()
    write_path: bool = False


@dataclass(slots=True, frozen=True)
class DockManifest:
    """Repository-level declarative dock specification (Rule 12)."""

    name: str
    description: str
    declared: bool
    manifest_path: str | None
    sha256: str
    entrypoints: dict[str, DockProcedure]
    tools: tuple[str, ...]
    permissions: DockPermissions
    boundaries: DockBoundaries
    warnings: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class DockLinkRecord:
    """Persistent ledger record of a linked agent dock (Rule 12)."""

    dock_name: str
    repo_source: str
    repo_path: str
    transport: str
    declared: bool
    manifest_sha256: str
    approved: bool
    approved_sha256: str
    linked_at: str


@dataclass(slots=True, frozen=True)
class DockStepResult:
    """Result of executing an individual procedure step (Rule 12)."""

    step_index: int
    command: str
    workdir: str
    returncode: int
    stdout: str
    stderr: str
    success: bool
    duration_seconds: float = 0.0
    called_procedure: str | None = None


@dataclass(slots=True, frozen=True)
class DockRunResult:
    """Aggregated outcome of executing a procedure on a dock (Rule 12)."""

    dock_name: str
    procedure_name: str
    success: bool
    steps: tuple[DockStepResult, ...] = ()
    error: str | None = None
    failed_step_index: int | None = None
    failed_step_command: str | None = None
    dry_run: bool = False
    total_duration_seconds: float = 0.0


class DockError(Exception):
    """Base exception for all agent dock operations."""


class DockManifestError(DockError):
    """Raised when dock manifest is malformed, missing required fields, or unparseable."""

    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = str(path)
        self.reason = reason
        super().__init__(f"Dock manifest error in '{path}': {reason}")


class DockApprovalDriftError(DockError):
    """Raised when live dock.yaml sha256 does not match approved_sha256."""

    def __init__(self, dock_name: str, live_sha: str, approved_sha: str) -> None:
        self.dock_name = dock_name
        self.live_sha = live_sha
        self.approved_sha = approved_sha
        super().__init__(
            f"Approval drift detected for dock '{dock_name}'. "
            f"Live manifest SHA ({live_sha[:12] if live_sha else 'empty'}) differs from approved SHA ({approved_sha[:12] if approved_sha else 'none'}). "
            f"Re-link with 'harness dock link <repo> --approve' to proceed."
        )


class DockBoundaryViolationError(DockError):
    """Raised when a procedure step violates boundary paths, operations, or workdir confinement."""


class DockPermissionError(DockError):
    """Raised when a requested action or procedure exceeds declared/approved permissions."""


class DockProcedureCycleError(DockError):
    """Raised when circular procedure composition is detected."""


class DockNotFoundError(DockError):
    """Raised when a named dock is not found in linked records."""


__all__ = [
    "DockPermissions",
    "DockBoundaries",
    "DockStep",
    "DockProcedure",
    "DockManifest",
    "DockLinkRecord",
    "DockStepResult",
    "DockRunResult",
    "DockError",
    "DockManifestError",
    "DockApprovalDriftError",
    "DockBoundaryViolationError",
    "DockPermissionError",
    "DockProcedureCycleError",
    "DockNotFoundError",
]
