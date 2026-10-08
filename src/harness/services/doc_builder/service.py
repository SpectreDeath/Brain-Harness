"""Typed Service Protocol, Default Implementation, and Single-Seam Resolver for doc_builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.doc_builder.engine import DocBuilderDomainEngine
from harness.services.doc_builder.models import (
    AutodocSignature,
    DocChunk,
    DocFormatConvertResult,
    DocLintResult,
    LinkValidationReport,
)


@runtime_checkable
class HfDocBuilderProtocol(Protocol):
    """Protocol for Hugging Face doc-builder operations."""

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        """Extract structured signature, parameters, and docstrings from Python object."""
        ...

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        """Verify internal relative links, anchors, and table-of-contents integrity."""
        ...

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        """Convert Markdown, RST, or IPYNB to MDX with Svelte tags."""
        ...

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        """Lint and format code examples inside docstrings and MDX."""
        ...

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        """Hierarchically chunk markdown by headings for embedding indexation."""
        ...


class DefaultHfDocBuilderService(HfDocBuilderProtocol):
    """Authoritative in-process service implementation wrapping doc builder domain logic."""

    def __init__(self, engine: Any | None = None) -> None:
        self._engine = engine or DocBuilderDomainEngine

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        return self._engine.inspect_autodoc(
            package_name, object_name, mock_heavy_deps, source_file
        )

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        return self._engine.verify_links(docs_dir, check_anchors, check_toc)

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        return self._engine.convert_format(source_path, target_format)

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        return self._engine.lint_style(file_path, fix)

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        return self._engine.chunk_markdown(markdown_text, page_title, max_chunk_size)


# Backward compatibility class alias
HfDocBuilderService = DefaultHfDocBuilderService

DOC_BUILDER_SERVICE_KEY: ServiceKey[HfDocBuilderProtocol] = ServiceKey(
    "service.doc_builder"
)


def resolve_doc_builder(
    context: ServiceContext | None = None,
) -> HfDocBuilderProtocol:
    """Rule 58: Single-seam resolver with standalone fallback for HfDocBuilderProtocol."""
    if context is not None:
        svc = context.optional(DOC_BUILDER_SERVICE_KEY)
        if svc is not None and isinstance(svc, HfDocBuilderProtocol):
            return svc

    return DefaultHfDocBuilderService()


__all__ = [
    "DOC_BUILDER_SERVICE_KEY",
    "DefaultHfDocBuilderService",
    "HfDocBuilderProtocol",
    "HfDocBuilderService",
    "resolve_doc_builder",
]
