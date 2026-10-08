"""Codebase Context Engine — Qualified Script Facade (Rule 57).

Re-exports slotted domain models and engine from the micro-kernel service
harness.services.codebase_context to avoid generic module name collisions in sys.modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on sys.path if running in standalone script mode
_ws_root = Path(__file__).resolve().parent.parent.parent.parent
_src = _ws_root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from harness.services.codebase_context import (
    CheckResult,
    CodebaseContextService,
    ConfigResolver,
    ContextGovernanceReport,
    ContextLintReport,
    ContextSmellViolation,
    DefaultCodebaseContextService,
    GovernanceStageResult,
    ManifestScriptInspector,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SemanticPathClassifier,
    SyncDriftCheck,
    SyncResult,
    TokenBudgetCheck,
    resolve_codebase_context,
)

# Backward-compatibility alias
CodebaseContextEngine = DefaultCodebaseContextService

__all__ = [
    "CheckResult",
    "CodebaseContextEngine",
    "CodebaseContextService",
    "ConfigResolver",
    "ContextGovernanceReport",
    "ContextLintReport",
    "ContextSmellViolation",
    "DefaultCodebaseContextService",
    "GovernanceStageResult",
    "ManifestScriptInspector",
    "PathIntegrityCheck",
    "ScriptIntegrityCheck",
    "SemanticPathClassifier",
    "SyncDriftCheck",
    "SyncResult",
    "TokenBudgetCheck",
    "resolve_codebase_context",
]
