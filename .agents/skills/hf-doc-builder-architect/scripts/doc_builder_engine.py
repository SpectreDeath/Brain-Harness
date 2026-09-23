"""Domain engine implementing HF Doc Builder architecture with slotted/frozen models.

Backward-compatible forwarding adapter delegating to harness.services.doc_builder (Rule 49).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Rule 23: UTF-8 stream output on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Ensure harness is on sys.path if invoked standalone
_REPO_ROOT = Path(__file__).resolve().parents[4]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.services.doc_builder import (
    AutodocParameter,
    AutodocSignature,
    DefaultHfDocBuilderService,
    DocAstStaticAnalyzer,
    DocBuilderDomainEngine,
    DocChunk,
    DocFormatConvertResult,
    DocLintResult,
    LinkDiagnostic,
    LinkValidationReport,
    MockModule,
    TocDiagnostic,
    TocIntegrityAuditor,
    ZeroDepMockLoader,
    virtualize_imports,
)
from harness.services.doc_builder import (
    ZeroDepMockFinder as MockFinder,
)

__all__ = [
    "AutodocParameter",
    "AutodocSignature",
    "DefaultHfDocBuilderService",
    "DocAstStaticAnalyzer",
    "DocBuilderDomainEngine",
    "DocChunk",
    "DocFormatConvertResult",
    "DocLintResult",
    "LinkDiagnostic",
    "LinkValidationReport",
    "MockFinder",
    "MockModule",
    "TocDiagnostic",
    "TocIntegrityAuditor",
    "ZeroDepMockLoader",
    "virtualize_imports",
]
