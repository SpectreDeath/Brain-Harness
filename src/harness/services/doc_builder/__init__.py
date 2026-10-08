"""Hugging Face Doc Builder service package facade.

Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
Rule 49: Authoritative in-memory domain engine for micro-kernel IoC elevation.
Rule 58: Single-seam resolver with standalone fallback.
"""

from __future__ import annotations

import sys

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.doc_builder.ast_analyzer import (
    DocAstStaticAnalyzer,
    TocIntegrityAuditor,
)
from harness.services.doc_builder.engine import (
    DocBuilderDomainEngine,
)
from harness.services.doc_builder.models import (
    AutodocParameter,
    AutodocSignature,
    AutodocSignatureData,
    DocChunk,
    DocChunkData,
    DocFormatConvertData,
    DocFormatConvertResult,
    DocLintResult,
    DocLintResultData,
    LinkDiagnostic,
    LinkDiagnosticData,
    LinkValidationReport,
    LinkValidationReportData,
    TocDiagnostic,
)
from harness.services.doc_builder.service import (
    DOC_BUILDER_SERVICE_KEY,
    DefaultHfDocBuilderService,
    HfDocBuilderProtocol,
    HfDocBuilderService,
    resolve_doc_builder,
)
from harness.services.doc_builder.virtualizer import (
    MockModule,
    ZeroDepMockFinder,
    ZeroDepMockLoader,
    virtualize_imports,
)

__all__ = [
    "DOC_BUILDER_SERVICE_KEY",
    "AutodocParameter",
    "AutodocSignature",
    "AutodocSignatureData",
    "DefaultHfDocBuilderService",
    "DocAstStaticAnalyzer",
    "DocBuilderDomainEngine",
    "DocChunk",
    "DocChunkData",
    "DocFormatConvertData",
    "DocFormatConvertResult",
    "DocLintResult",
    "DocLintResultData",
    "HfDocBuilderProtocol",
    "HfDocBuilderService",
    "LinkDiagnostic",
    "LinkDiagnosticData",
    "LinkValidationReport",
    "LinkValidationReportData",
    "MockModule",
    "TocDiagnostic",
    "TocIntegrityAuditor",
    "ZeroDepMockFinder",
    "ZeroDepMockLoader",
    "resolve_doc_builder",
    "virtualize_imports",
]
