"""Codebase Context Service modular package facade."""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from .classifier import SemanticPathClassifier
from .config import ConfigResolver
from .governor import ContextGovernor
from .linter import ContextLinter
from .manifest import ManifestScriptInspector
from .models import (
    CheckResult,
    ContextGovernanceReport,
    ContextLintReport,
    ContextSmellViolation,
    GovernanceStageResult,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SyncDriftCheck,
    SyncResult,
    TokenBudgetCheck,
)
from .protocol import CODEBASE_CONTEXT_SERVICE_KEY, CodebaseContextService
from .resolvers import resolve_codebase_context
from .service import DefaultCodebaseContextService
from .synchronizer import BANNER_TEMPLATE, DEFAULT_CLAUDE_EXTRAS, ContextSynchronizer

__all__ = [
    "BANNER_TEMPLATE",
    "CODEBASE_CONTEXT_SERVICE_KEY",
    "CheckResult",
    "CodebaseContextService",
    "ConfigResolver",
    "ContextGovernanceReport",
    "ContextGovernor",
    "ContextLintReport",
    "ContextLinter",
    "ContextSmellViolation",
    "ContextSynchronizer",
    "DEFAULT_CLAUDE_EXTRAS",
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
