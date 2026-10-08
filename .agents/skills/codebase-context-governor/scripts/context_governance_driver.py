"""Codebase Context Governance Driver — runtime execution engine for context governance.

Coordinates:
    1. Context rot and smell detection (bloat, lint leakage, contradictions)
    2. Three-layer context partitioning validation
    3. SSOT manifest synchronization verification
    4. Headless CI linter execution (Rule 10 & Rule 11)
    5. Dynamic 5D compute complexity routing (Rule 25)

Delegates to authoritative micro-kernel service harness.services.codebase_context (Rule 49 & Rule 57).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure src is on sys.path for harness package resolution
_ws_root = Path(__file__).resolve().parent.parent.parent.parent
_src = _ws_root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from harness.services.codebase_context import (
    ContextGovernanceReport,
    ContextSmellViolation,
    DefaultCodebaseContextService,
    GovernanceStageResult,
)


class ContextGovernanceDriver:
    """Coordinates the 5-stage context governance pipeline."""

    def __init__(self, workspace_root: Path | str) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self._service = DefaultCodebaseContextService(root=self.workspace_root)

    def audit_smells(self, target_file: Path | str | None = None) -> tuple[GovernanceStageResult, list[ContextSmellViolation]]:
        """Stage 1: Scan target instruction file for line-count bloat and lint leakage."""
        return self._service.audit_smells(target_file=target_file)

    def verify_partitioning(self) -> GovernanceStageResult:
        """Stage 2: Validate three-layer context boundaries."""
        return self._service.verify_partitioning()

    def verify_synchronization(self) -> GovernanceStageResult:
        """Stage 3: Confirm derived context files are in sync with primary manifests."""
        return self._service.verify_synchronization()

    def run_ci_lint(self, max_violations: int = 0) -> GovernanceStageResult:
        """Stage 4: Execute automated CI linter gate."""
        return self._service.run_ci_lint()

    def assess_compute_tier(self, complexity_score: float = 0.5) -> tuple[GovernanceStageResult, str]:
        """Stage 5: Evaluate 5D complexity and route optimal model reasoning tier (Rule 25)."""
        return self._service.assess_compute_tier(complexity_score=complexity_score)

    def execute_governance_cycle(
        self,
        target_file: Path | str | None = None,
        complexity_score: float = 0.5,
    ) -> ContextGovernanceReport:
        """Run full 5-stage context governance pipeline."""
        return self._service.govern(target_file=target_file, complexity_score=complexity_score)


__all__ = [
    "ContextGovernanceDriver",
    "ContextGovernanceReport",
    "ContextSmellViolation",
    "GovernanceStageResult",
]
