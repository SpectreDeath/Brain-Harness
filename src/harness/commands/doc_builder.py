"""Headless Click CLI commands for Hugging Face Doc Builder operations.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext
from harness.services.doc_builder import (
    DOC_BUILDER_SERVICE_KEY,
    DefaultHfDocBuilderService,
    HfDocBuilderProtocol,
)

logger = structlog.get_logger(__name__)


def get_doc_builder_service(
    context: ServiceContext | None = None,
) -> HfDocBuilderProtocol:
    """Retrieve or bootstrap the HfDocBuilderProtocol service instance."""
    if context is not None:
        svc = context.optional(DOC_BUILDER_SERVICE_KEY)
        if svc is not None:
            return svc

    try:
        from plugins.developer_tooling.hf_doc_builder.main import plugin as doc_plugin

        return doc_plugin
    except Exception as exc:
        logger.debug("hf_doc_builder_plugin_fallback_failed", error=str(exc))
        return DefaultHfDocBuilderService()


def inspect_autodoc_cmd(
    package_name: str,
    object_name: str,
    mock_heavy_deps: bool = True,
    source_file: str | None = None,
    service: HfDocBuilderProtocol | None = None,
) -> dict[str, Any]:
    """Execute autodoc extraction on a Python package or source file."""
    svc = service or get_doc_builder_service()
    res = svc.inspect_autodoc(
        package_name=package_name,
        object_name=object_name,
        mock_heavy_deps=mock_heavy_deps,
        source_file=source_file,
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
        "docstring_format": res.docstring_format,
        "code_examples": list(res.code_examples),
    }


def verify_links_cmd(
    docs_dir: str | Path,
    check_anchors: bool = True,
    check_toc: bool = True,
    service: HfDocBuilderProtocol | None = None,
) -> dict[str, Any]:
    """Execute documentation link, anchor, and TOC integrity verification."""
    svc = service or get_doc_builder_service()
    res = svc.verify_links(
        docs_dir=docs_dir, check_anchors=check_anchors, check_toc=check_toc
    )
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


def convert_format_cmd(
    source_path: str | Path,
    target_format: str = "mdx",
    service: HfDocBuilderProtocol | None = None,
) -> dict[str, Any]:
    """Transpile Markdown, RST, or IPYNB to MDX format."""
    svc = service or get_doc_builder_service()
    res = svc.convert_format(source_path=source_path, target_format=target_format)
    return {
        "source_path": res.source_path,
        "target_format": res.target_format,
        "converted_content": res.converted_content,
        "svelte_components_injected": list(res.svelte_components_injected),
    }


def lint_style_cmd(
    file_path: str | Path,
    fix: bool = False,
    service: HfDocBuilderProtocol | None = None,
) -> dict[str, Any]:
    """Lint and format code examples inside docstrings and MDX files."""
    svc = service or get_doc_builder_service()
    res = svc.lint_style(file_path=file_path, fix=fix)
    return {
        "file_path": res.file_path,
        "issues_count": res.issues_count,
        "diagnostics": list(res.diagnostics),
        "formatted_content": res.formatted_content,
    }


def chunk_markdown_cmd(
    markdown_text: str,
    page_title: str = "Documentation",
    max_chunk_size: int = 1500,
    service: HfDocBuilderProtocol | None = None,
) -> list[dict[str, Any]]:
    """Hierarchically partition Markdown text along heading trees with breadcrumbs."""
    svc = service or get_doc_builder_service()
    chunks = svc.chunk_markdown(
        markdown_text=markdown_text,
        page_title=page_title,
        max_chunk_size=max_chunk_size,
    )
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


# ---------------------------------------------------------------------------
# Click CLI Seam (Rule 6 & Rule 10)
# ---------------------------------------------------------------------------


@click.group("doc-builder")
def doc_builder_group() -> None:
    """HF Doc Builder — Documentation compilation, link verification, and MDX transpilation."""


@doc_builder_group.command("inspect")
@click.option(
    "--package", "-p", "package_name", required=True, help="Target Python package name"
)
@click.option(
    "--object",
    "-o",
    "object_name",
    required=True,
    help="Target class, function, or method name",
)
@click.option(
    "--mock-heavy/--no-mock",
    default=True,
    help="Intercept heavy dependencies via sys.meta_path",
)
@click.option(
    "--source-file",
    "-s",
    default=None,
    help="Optional Python source file for static AST parsing",
)
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def doc_inspect_cli(
    package_name: str,
    object_name: str,
    mock_heavy: bool,
    source_file: str | None,
    json_output: bool,
) -> None:
    """Extract structured signatures, parameters, and docstrings from Python objects."""
    result = inspect_autodoc_cmd(
        package_name=package_name,
        object_name=object_name,
        mock_heavy_deps=mock_heavy,
        source_file=source_file,
    )
    if json_output:
        click.echo(_json.dumps(result, indent=2))
    else:
        click.echo(f"Signature: {result['signature_str']}")
        click.echo(f"Return Type: {result['return_type']}")
        click.echo(f"Parameters ({len(result['parameters'])}):")
        for p in result["parameters"]:
            def_str = f" = {p['default_value']}" if p["default_value"] else ""
            click.echo(f"  - {p['name']}: {p['type_annotation']}{def_str}")
        if result["docstring"]:
            click.echo(f"\nDocstring:\n{result['docstring']}")


@doc_builder_group.command("verify")
@click.option(
    "--docs-dir", "-d", default="docs", help="Path to documentation root directory"
)
@click.option(
    "--anchors/--no-anchors", default=True, help="Verify heading anchor fragments"
)
@click.option(
    "--toc/--no-toc",
    default=True,
    help="Verify table-of-contents integrity and orphan pages",
)
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def doc_verify_cli(
    docs_dir: str,
    anchors: bool,
    toc: bool,
    json_output: bool,
) -> None:
    """Verify internal documentation links, anchor targets, and TOC completeness."""
    result = verify_links_cmd(docs_dir=docs_dir, check_anchors=anchors, check_toc=toc)
    if json_output:
        click.echo(_json.dumps(result, indent=2))
    else:
        status_sym = "✓" if result["valid"] else "✗"
        click.echo(
            f"Scanned {result['scanned_files_count']} files, checked {result['total_links_checked']} links."
        )
        if result["valid"]:
            click.echo(f"{status_sym} All links and TOC entries are valid.")
        else:
            click.echo(f"{status_sym} Validation failed:")
            for b in result["broken_links"]:
                click.echo(
                    f"  [Broken Link] {b['source_file']}:{b['line_number']} -> {b['target_link']} ({b['error_reason']})"
                )
            for t in result["toc_diagnostics"]:
                if not t["is_valid"]:
                    click.echo(
                        f"  [Broken TOC Entry] {t['entry']}: {t['error_reason']}"
                    )
            for o in result["orphaned_files"]:
                click.echo(f"  [Orphan Page] {o} is not listed in _toctree.yml")
        if not result["valid"]:
            sys.exit(1)


@doc_builder_group.command("convert")
@click.option(
    "--source",
    "-s",
    "source_path",
    required=True,
    help="Path to source document or raw markdown string",
)
@click.option(
    "--format", "-f", "target_format", default="mdx", help="Target output format"
)
@click.option(
    "--output", "-o", "output_path", default=None, help="Optional output file path"
)
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def doc_convert_cli(
    source_path: str,
    target_format: str,
    output_path: str | None,
    json_output: bool,
) -> None:
    """Transpile Markdown, RST, or IPYNB into MDX with Svelte tags."""
    result = convert_format_cmd(source_path=source_path, target_format=target_format)
    if output_path:
        Path(output_path).write_text(result["converted_content"], encoding="utf-8")
        click.echo(f"Written converted MDX to: {output_path}")
    elif json_output:
        click.echo(_json.dumps(result, indent=2))
    else:
        click.echo(result["converted_content"])


@doc_builder_group.command("lint")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    help="Path to documentation file to lint",
)
@click.option("--fix", is_flag=True, help="Automatically format and fix issues")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def doc_lint_cli(
    file_path: str,
    fix: bool,
    json_output: bool,
) -> None:
    """Lint and format code examples inside docstrings and MDX files."""
    result = lint_style_cmd(file_path=file_path, fix=fix)
    if json_output:
        click.echo(_json.dumps(result, indent=2))
    else:
        click.echo(f"Found {result['issues_count']} issues in {result['file_path']}")
        for d in result["diagnostics"]:
            click.echo(f"  - {d}")
        if fix and result["formatted_content"] is not None:
            Path(file_path).write_text(result["formatted_content"], encoding="utf-8")
            click.echo(f"Fixed issues in {file_path}")


@doc_builder_group.command("chunk")
@click.option("--text", "-t", default=None, help="Markdown text to chunk")
@click.option("--file", "-f", default=None, help="Path to markdown file to chunk")
@click.option("--title", default="Documentation", help="Top-level title of document")
@click.option(
    "--max-size", default=1500, type=int, help="Maximum character size per chunk"
)
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
def doc_chunk_cli(
    text: str | None,
    file: str | None,
    title: str,
    max_size: int,
    json_output: bool,
) -> None:
    """Hierarchically partition documentation along heading trees for vector search."""
    if file:
        content = Path(file).read_text(encoding="utf-8", errors="ignore")
    elif text:
        content = text
    else:
        raise click.UsageError("Must provide either --text or --file")

    result = chunk_markdown_cmd(
        markdown_text=content,
        page_title=title,
        max_chunk_size=max_size,
    )
    if json_output:
        click.echo(_json.dumps(result, indent=2))
    else:
        click.echo(f"Generated {len(result)} chunks:")
        for c in result:
            crumbs = " > ".join(c["breadcrumb"])
            click.echo(
                f"  [{c['chunk_id']}] (Level {c['heading_level']}) {crumbs} ({c['tokens_estimate']} tokens)"
            )
