"""Domain models for Hugging Face Doc Builder service.

Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AutodocParameter:
    """Immutable parameter definition extracted from AST / type hints."""

    name: str
    type_annotation: str = "Any"
    default_value: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("AutodocParameter.name cannot be empty")


@dataclass(slots=True, frozen=True)
class AutodocSignature:
    """Immutable structured signature and docstring payload."""

    object_path: str
    signature_str: str
    parameters: tuple[AutodocParameter, ...] = field(default_factory=tuple)
    return_type: str = "None"
    docstring: str = ""
    docstring_format: str = "markdown"
    code_examples: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.object_path or not self.object_path.strip():
            raise ValueError("AutodocSignature.object_path cannot be empty")


@dataclass(slots=True, frozen=True)
class LinkDiagnostic:
    """Diagnostic entry for a single link or anchor check."""

    source_file: str
    target_link: str
    anchor: str | None = None
    is_valid: bool = True
    line_number: int = 1
    error_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.source_file or not self.source_file.strip():
            raise ValueError("LinkDiagnostic.source_file cannot be empty")
        if not self.target_link or not self.target_link.strip():
            raise ValueError("LinkDiagnostic.target_link cannot be empty")


@dataclass(slots=True, frozen=True)
class TocDiagnostic:
    """Diagnostic entry for table-of-contents integrity checks."""

    entry: str
    file_path: str | None = None
    is_valid: bool = True
    error_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.entry or not self.entry.strip():
            raise ValueError("TocDiagnostic.entry cannot be empty")


@dataclass(slots=True, frozen=True)
class LinkValidationReport:
    """Aggregated link and table-of-contents validation report."""

    scanned_files_count: int = 0
    total_links_checked: int = 0
    broken_links: tuple[LinkDiagnostic, ...] = field(default_factory=tuple)
    toc_diagnostics: tuple[TocDiagnostic, ...] = field(default_factory=tuple)
    orphaned_files: tuple[str, ...] = field(default_factory=tuple)
    valid: bool = True


@dataclass(slots=True, frozen=True)
class DocFormatConvertResult:
    """Result of converting a document into MDX format with Svelte tags."""

    source_path: str
    target_format: str = "mdx"
    converted_content: str = ""
    svelte_components_injected: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source_path or not self.source_path.strip():
            raise ValueError("DocFormatConvertResult.source_path cannot be empty")


@dataclass(slots=True, frozen=True)
class DocLintResult:
    """Result of styling / linting code examples in documentation."""

    file_path: str
    issues_count: int = 0
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    formatted_content: str | None = None

    def __post_init__(self) -> None:
        if not self.file_path or not self.file_path.strip():
            raise ValueError("DocLintResult.file_path cannot be empty")


@dataclass(slots=True, frozen=True)
class DocChunk:
    """Heading-anchored documentation chunk for search / embeddings."""

    chunk_id: str
    title: str
    heading_level: int
    content: str
    tokens_estimate: int = 0
    breadcrumb: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("DocChunk.chunk_id cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("DocChunk.title cannot be empty")


# Backward compatibility aliases for existing callers
AutodocSignatureData = AutodocSignature
LinkDiagnosticData = LinkDiagnostic
LinkValidationReportData = LinkValidationReport
DocFormatConvertData = DocFormatConvertResult
DocLintResultData = DocLintResult
DocChunkData = DocChunk

__all__ = [
    "AutodocParameter",
    "AutodocSignature",
    "AutodocSignatureData",
    "DocChunk",
    "DocChunkData",
    "DocFormatConvertData",
    "DocFormatConvertResult",
    "DocLintResult",
    "DocLintResultData",
    "LinkDiagnostic",
    "LinkDiagnosticData",
    "LinkValidationReport",
    "LinkValidationReportData",
    "TocDiagnostic",
]
