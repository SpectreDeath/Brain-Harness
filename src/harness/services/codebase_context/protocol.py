"""Service protocol definition and typed ServiceKey for CodebaseContextService."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from .models import ContextGovernanceReport, ContextLintReport, GovernanceStageResult, SyncResult


@runtime_checkable
class CodebaseContextService(Protocol):
    """Protocol for repository context architecture, linting, and 5-stage governance."""

    def lint(self, root: str | Path = ".") -> ContextLintReport:
        """Verify repository context files across token, path, script, and drift dimensions."""
        ...

    def sync(self, root: str | Path = ".", source_rel: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
        """Synchronize downstream vendor context files against canonical source."""
        ...

    def govern(
        self,
        root: str | Path = ".",
        target_file: str | Path | None = None,
        complexity_score: float = 0.5,
    ) -> ContextGovernanceReport:
        """Execute complete 5-stage context governance pipeline."""
        ...

    def assess_compute_tier(self, complexity_score: float = 0.5) -> tuple[GovernanceStageResult, str]:
        """Evaluate 5D complexity and route optimal model reasoning tier (Rule 25)."""
        ...


CODEBASE_CONTEXT_SERVICE_KEY: ServiceKey[CodebaseContextService] = ServiceKey(
    "harness.services.codebase_context"
)
