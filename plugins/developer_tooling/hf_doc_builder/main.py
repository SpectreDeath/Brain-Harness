"""Hugging Face Doc Builder Plugin — AST autodoc, link checking, and MDX chunking."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 stream reconfigure
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"

if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from service import HfDocBuilderSubprocessService

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.doc_builder import (
    DOC_BUILDER_SERVICE_KEY,
    AutodocSignature,
    DocChunk,
    DocFormatConvertResult,
    DocLintResult,
    HfDocBuilderProtocol,
    LinkValidationReport,
)

logger = structlog.get_logger(__name__)


class HfDocBuilderPlugin(HarnessPlugin, HfDocBuilderProtocol):
    """Plugin implementing HfDocBuilderProtocol with typed IoC registration (Rule 45)."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._service = HfDocBuilderSubprocessService(root_dir=self._root)

    @property
    def name(self) -> str:
        return "plugin.hf_doc_builder"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Hugging Face doc-builder integration for AST autodoc inspection, "
            "deterministic link checking, MDX transpilation, and semantic chunking"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DOC_BUILDER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self into IoC container (Rule 2, Rule 45)."""
        context.provide(DOC_BUILDER_SERVICE_KEY, self)
        logger.info(
            "hf_doc_builder_service_provided",
            service=str(DOC_BUILDER_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- HfDocBuilderProtocol implementation ---

    def inspect_autodoc(
        self,
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        return self._service.inspect_autodoc(
            package_name, object_name, mock_heavy_deps, source_file
        )

    def verify_links(
        self,
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        return self._service.verify_links(docs_dir, check_anchors, check_toc)

    def convert_format(
        self,
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        return self._service.convert_format(source_path, target_format)

    def lint_style(
        self,
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        return self._service.lint_style(file_path, fix)

    def chunk_markdown(
        self,
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        return self._service.chunk_markdown(markdown_text, page_title, max_chunk_size)


# Rule 45: Export instantiated module singleton
plugin = HfDocBuilderPlugin()


# Top-level entrypoints matching plugin.json tool declarations
def doc_autodoc_inspect(
    package_name: str,
    object_name: str,
    mock_heavy_deps: bool = True,
    source_file: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    res = plugin.inspect_autodoc(
        package_name, object_name, mock_heavy_deps, source_file
    )
    return {
        "object_path": res.object_path,
        "signature_str": res.signature_str,
        "parameters": [
            {
                "name": p.name,
                "type_annotation": p.type_annotation,
                "default_value": p.default_value,
                "description": p.description,
            }
            for p in res.parameters
        ],
        "return_type": res.return_type,
        "docstring": res.docstring,
    }


def doc_link_verify(
    docs_dir: str,
    check_anchors: bool = True,
    check_toc: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    res = plugin.verify_links(docs_dir, check_anchors, check_toc)
    return {
        "scanned_files_count": res.scanned_files_count,
        "total_links_checked": res.total_links_checked,
        "valid": res.valid,
        "broken_links": [
            {
                "source_file": b.source_file,
                "target_link": b.target_link,
                "anchor": b.anchor,
                "line_number": b.line_number,
                "error_reason": b.error_reason,
            }
            for b in res.broken_links
        ],
        "toc_diagnostics": [
            {
                "entry": t.entry,
                "file_path": t.file_path,
                "is_valid": t.is_valid,
                "error_reason": t.error_reason,
            }
            for t in res.toc_diagnostics
        ],
        "orphaned_files": list(res.orphaned_files),
    }


def doc_format_convert(
    source_path: str,
    target_format: str = "mdx",
    **kwargs: Any,
) -> dict[str, Any]:
    res = plugin.convert_format(source_path, target_format)
    return {
        "source_path": res.source_path,
        "target_format": res.target_format,
        "converted_content": res.converted_content,
        "svelte_components_injected": list(res.svelte_components_injected),
    }


def doc_style_lint(
    file_path: str,
    fix: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    res = plugin.lint_style(file_path, fix)
    return {
        "file_path": res.file_path,
        "issues_count": res.issues_count,
        "diagnostics": list(res.diagnostics),
        "formatted_content": res.formatted_content,
    }


def doc_chunk_indexer(
    markdown_text: str,
    page_title: str = "Documentation",
    max_chunk_size: int = 1500,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    chunks = plugin.chunk_markdown(markdown_text, page_title, max_chunk_size)
    return [
        {
            "chunk_id": c.chunk_id,
            "title": c.title,
            "heading_level": c.heading_level,
            "tokens_estimate": c.tokens_estimate,
            "breadcrumb": list(c.breadcrumb),
            "content": c.content,
        }
        for c in chunks
    ]
