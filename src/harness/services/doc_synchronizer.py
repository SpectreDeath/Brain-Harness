"""DocSynchronizer service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ModuleDocStatusData(BaseModel):
    """Documentation coverage status for a single Python module."""

    module_path: str = Field(
        ..., description="Path to Python module relative to scanned root"
    )
    module_name: str = Field(..., description="Python module name")
    has_module_docstring: bool = Field(
        default=False, description="Whether module has a top-level docstring"
    )
    total_symbols: int = Field(
        default=0, description="Total public symbols (classes + methods + functions)"
    )
    documented_symbols: int = Field(
        default=0, description="Public symbols with non-empty docstrings"
    )
    dedicated_doc_path: str | None = Field(
        default=None,
        description="Relative path to dedicated markdown documentation file if found",
    )
    coverage_pct: float = Field(
        default=0.0,
        description="Calculated documentation coverage percentage 0.0-100.0",
    )


class DocCoverageReportData(BaseModel):
    """Repository-wide documentation coverage report."""

    scanned_root: str = Field(
        ..., description="Root directory scanned for documentation coverage"
    )
    total_modules: int = Field(default=0, description="Total Python modules inspected")
    modules_with_docstring: int = Field(
        default=0, description="Number of modules with top-level docstrings"
    )
    total_symbols: int = Field(
        default=0, description="Total public symbols found across all modules"
    )
    documented_symbols: int = Field(
        default=0, description="Total documented public symbols across all modules"
    )
    overall_coverage_pct: float = Field(
        default=0.0,
        description="Aggregate repository documentation coverage percentage",
    )
    min_passing_score: float = Field(
        default=80.0, description="Minimum acceptable documentation coverage threshold"
    )
    passed: bool = Field(
        default=True,
        description="Whether overall coverage meets or exceeds min_passing_score",
    )
    missing_docs: list[str] = Field(
        default_factory=list,
        description="List of modules missing documentation or below threshold",
    )
    modules: list[ModuleDocStatusData] = Field(
        default_factory=list, description="Detailed per-module status breakdowns"
    )


class BrokenLinkData(BaseModel):
    """Broken relative link identified inside Markdown documentation."""

    source_file: str = Field(
        ..., description="Markdown document containing the broken link"
    )
    target_link: str = Field(
        ..., description="Link target expression as written in markdown"
    )
    line_number: int = Field(
        ..., description="1-indexed line number where broken link occurs"
    )
    reason: str = Field(..., description="Diagnostic rationale why link is broken")


class StaleSymbolData(BaseModel):
    """Stale or non-existent code symbol identified inside Markdown documentation."""

    source_file: str = Field(
        ..., description="Markdown document referencing the symbol"
    )
    symbol_name: str = Field(
        ..., description="Referenced symbol identifier (class, function, method)"
    )
    line_number: int = Field(
        ..., description="1-indexed line number where stale symbol occurs"
    )
    reason: str = Field(
        ..., description="Diagnostic explanation why symbol is considered stale"
    )


class DocDriftReportData(BaseModel):
    """Documentation drift verification report covering links and code symbols."""

    scanned_docs_count: int = Field(
        default=0, description="Number of markdown files verified for drift"
    )
    broken_links: list[BrokenLinkData] = Field(
        default_factory=list, description="Detected broken relative links"
    )
    stale_symbols: list[StaleSymbolData] = Field(
        default_factory=list, description="Detected stale code symbol references"
    )
    has_drift: bool = Field(
        default=False,
        description="Whether any broken links or stale symbols were discovered",
    )


@runtime_checkable
class DocSynchronizerService(Protocol):
    """Protocol for documentation auditing, symbol drift verification, and Diataxis scaffolding."""

    def audit(
        self,
        target_dir: str | Path | None = None,
        min_coverage: float = 80.0,
        exclude_patterns: list[str] | None = None,
    ) -> DocCoverageReportData | Any:
        """Audit Python codebase and calculate documentation coverage metrics."""
        ...

    def drift_check(
        self,
        docs_dir: str | Path | None = None,
        check_symbols: bool = True,
    ) -> DocDriftReportData | Any:
        """Inspect markdown documents for broken relative links and stale AST symbol references."""
        ...

    def scaffold(
        self,
        module_path: str | Path,
        doc_type: str = "api",
        output_path: str | Path | None = None,
    ) -> Path:
        """Scaffold standardized Diataxis documentation for a Python module."""
        ...

    def visual_brief(
        self,
        target_dir: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and coverage metrics."""
        ...

    def get_cache_stats(self) -> dict[str, int]:
        """Return AST parsing cache statistics (hits, misses, cached_entries)."""
        ...


DOC_SYNCHRONIZER_SERVICE_KEY: ServiceKey[DocSynchronizerService] = ServiceKey(
    "service.doc_synchronizer"
)
