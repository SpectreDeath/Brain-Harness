"""Authoritative in-memory domain engine for documentation compilation and verification."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any

import structlog

from harness.services.doc_builder.ast_analyzer import (
    DocAstStaticAnalyzer,
    TocIntegrityAuditor,
)
from harness.services.doc_builder.models import (
    AutodocParameter,
    AutodocSignature,
    DocChunk,
    DocFormatConvertResult,
    DocLintResult,
    LinkDiagnostic,
    LinkValidationReport,
    TocDiagnostic,
)
from harness.services.doc_builder.virtualizer import virtualize_imports

logger = structlog.get_logger(__name__)

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DocBuilderDomainEngine:
    """Authoritative in-memory domain engine for documentation compilation and verification."""

    @staticmethod
    def inspect_autodoc(
        package_name: str,
        object_name: str,
        mock_heavy_deps: bool = True,
        source_file: str | Path | None = None,
    ) -> AutodocSignature:
        """Extract structured signature and parameters from a Python object or source file."""
        # 1. If explicit source_file provided, parse via static AST
        if source_file:
            p = Path(source_file)
            if p.exists():
                sigs = DocAstStaticAnalyzer.parse_source(
                    p.read_text(encoding="utf-8"), target_object=object_name
                )
                if sigs:
                    return sigs[0]

        # 2. Dynamic import with optional mock virtualization
        obj: Any = None
        try:
            if mock_heavy_deps:
                with virtualize_imports():
                    mod = importlib.import_module(package_name)
                    obj = getattr(mod, object_name)
            else:
                mod = importlib.import_module(package_name)
                obj = getattr(mod, object_name)
        except Exception as exc:
            logger.debug(
                "dynamic_import_fallback",
                package=package_name,
                object=object_name,
                error=str(exc),
            )
            # 3. Static AST fallback by finding module source if possible
            try:
                mod_spec = importlib.util.find_spec(package_name)
                if mod_spec and mod_spec.origin and Path(mod_spec.origin).exists():
                    sigs = DocAstStaticAnalyzer.parse_source(
                        Path(mod_spec.origin).read_text(
                            encoding="utf-8", errors="ignore"
                        ),
                        target_object=object_name,
                    )
                    if sigs:
                        return sigs[0]
            except Exception:
                pass

            # Safe static fallback signature
            return AutodocSignature(
                object_path=f"{package_name}.{object_name}",
                signature_str=f"{object_name}(*args, **kwargs)",
                parameters=(
                    AutodocParameter(
                        name="args",
                        type_annotation="tuple",
                        description="Positional arguments",
                    ),
                    AutodocParameter(
                        name="kwargs",
                        type_annotation="dict",
                        description="Keyword arguments",
                    ),
                ),
                return_type="Any",
                docstring=f"Documentation for {object_name} in {package_name}.",
                docstring_format="markdown",
                code_examples=(),
            )

        doc = inspect.getdoc(obj) or ""
        sig = None
        try:
            sig = inspect.signature(obj) if callable(obj) else None
        except Exception:
            sig = None
        sig_str = str(sig) if sig else "()"

        params: list[AutodocParameter] = []
        ret_type = "None"
        if sig:
            if sig.return_annotation is not inspect.Signature.empty:
                ret_type = str(sig.return_annotation)
            for p_name, param in sig.parameters.items():
                annotation = (
                    str(param.annotation)
                    if param.annotation is not inspect.Signature.empty
                    else "Any"
                )
                default = (
                    str(param.default)
                    if param.default is not inspect.Signature.empty
                    else None
                )
                params.append(
                    AutodocParameter(
                        name=p_name,
                        type_annotation=annotation,
                        default_value=default,
                        description=f"Parameter {p_name}",
                    )
                )

        return AutodocSignature(
            object_path=f"{package_name}.{object_name}",
            signature_str=f"{object_name}{sig_str}",
            parameters=tuple(params),
            return_type=ret_type,
            docstring=doc,
            docstring_format="markdown",
            code_examples=(),
        )

    @staticmethod
    def verify_links(
        docs_dir: str | Path,
        check_anchors: bool = True,
        check_toc: bool = True,
    ) -> LinkValidationReport:
        """Verify internal Markdown links, anchors, and TOC integrity across documentation."""
        target_path = Path(docs_dir)
        if not target_path.exists():
            return LinkValidationReport(
                scanned_files_count=0,
                total_links_checked=0,
                broken_links=(
                    LinkDiagnostic(
                        source_file=str(target_path),
                        target_link="",
                        is_valid=False,
                        error_reason=f"Docs directory does not exist: {target_path}",
                    ),
                ),
                valid=False,
            )

        md_files = list(target_path.rglob("*.md")) + list(target_path.rglob("*.mdx"))
        if not md_files and target_path.is_file():
            md_files = [target_path]

        # 1. Build anchor index across all files
        anchor_index: dict[str, set[str]] = {}
        file_rel_paths: set[str] = set()

        for mf in md_files:
            rel = str(
                mf.relative_to(
                    target_path if target_path.is_dir() else target_path.parent
                )
            ).replace("\\", "/")
            file_rel_paths.add(rel)
            base_rel = rel.rsplit(".", 1)[0]
            file_rel_paths.add(base_rel)

            text = mf.read_text(encoding="utf-8", errors="ignore")
            anchors: set[str] = set()
            for line in text.splitlines():
                if line.startswith("#"):
                    title = re.sub(r"^#+\s*", "", line).strip()
                    slug = (
                        re.sub(r"[^a-zA-Z0-9\-_ ]", "", title).lower().replace(" ", "-")
                    )
                    anchors.add(slug)
                for m in re.finditer(r'id=["\']([^"\']+)["\']', line):
                    anchors.add(m.group(1))
            anchor_index[rel] = anchors
            anchor_index[base_rel] = anchors

        # 2. Check links
        diagnostics: list[LinkDiagnostic] = []
        total_links = 0

        for mf in md_files:
            rel_src = str(
                mf.relative_to(
                    target_path if target_path.is_dir() else target_path.parent
                )
            ).replace("\\", "/")
            src_dir = str(Path(rel_src).parent).replace("\\", "/")
            text = mf.read_text(encoding="utf-8", errors="ignore")

            # Strip code fences before searching links
            clean_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

            for line_idx, line in enumerate(clean_text.splitlines(), start=1):
                for match in re.finditer(r"\[([^\]]*)\]\(([^\)]+)\)", line):
                    total_links += 1
                    target_link = match.group(2).strip()

                    # Skip external URLs
                    if target_link.startswith(
                        ("http://", "https://", "mailto:", "ftp:")
                    ):
                        continue

                    target_url, _, anchor = target_link.partition("#")
                    anchor = anchor.strip() if anchor else None

                    # Anchor-only link (#heading)
                    if not target_url:
                        if check_anchors and anchor:
                            current_anchors = anchor_index.get(rel_src, set())
                            if anchor not in current_anchors:
                                diagnostics.append(
                                    LinkDiagnostic(
                                        source_file=rel_src,
                                        target_link=target_link,
                                        anchor=anchor,
                                        is_valid=False,
                                        line_number=line_idx,
                                        error_reason=f"Anchor #{anchor} not found in {rel_src}",
                                    )
                                )
                        continue

                    # Resolve target path relative to source file
                    if target_url.startswith("/"):
                        resolved = target_url.lstrip("/")
                    else:
                        norm = os.path.normpath(
                            f"{src_dir}/{target_url}" if src_dir != "." else target_url
                        ).replace("\\", "/")
                        resolved = norm

                    resolved_clean = resolved.rstrip("/")
                    valid_file = (
                        resolved_clean in file_rel_paths
                        or f"{resolved_clean}.md" in file_rel_paths
                        or f"{resolved_clean}.mdx" in file_rel_paths
                        or f"{resolved_clean}/index.md" in file_rel_paths
                    )

                    if not valid_file:
                        diagnostics.append(
                            LinkDiagnostic(
                                source_file=rel_src,
                                target_link=target_link,
                                anchor=anchor,
                                is_valid=False,
                                line_number=line_idx,
                                error_reason=f"Target file path does not resolve: {target_url}",
                            )
                        )
                    elif check_anchors and anchor:
                        target_key = resolved_clean
                        if (
                            target_key not in anchor_index
                            and f"{resolved_clean}.md" in anchor_index
                        ):
                            target_key = f"{resolved_clean}.md"
                        target_anchors = anchor_index.get(target_key, set())
                        if target_anchors and anchor not in target_anchors:
                            diagnostics.append(
                                LinkDiagnostic(
                                    source_file=rel_src,
                                    target_link=target_link,
                                    anchor=anchor,
                                    is_valid=False,
                                    line_number=line_idx,
                                    error_reason=f"Anchor #{anchor} not found in target file {target_url}",
                                )
                            )

        # 3. Check Table of Contents integrity
        toc_diags: tuple[TocDiagnostic, ...] = ()
        orphans: tuple[str, ...] = ()
        if check_toc and target_path.is_dir():
            toc_diags, orphans = TocIntegrityAuditor.audit_toc(target_path)

        broken_toc_count = sum(1 for td in toc_diags if not td.is_valid)
        is_valid = len(diagnostics) == 0 and broken_toc_count == 0

        return LinkValidationReport(
            scanned_files_count=len(md_files),
            total_links_checked=total_links,
            broken_links=tuple(diagnostics),
            toc_diagnostics=toc_diags,
            orphaned_files=orphans,
            valid=is_valid,
        )

    @staticmethod
    def convert_format(
        source_path: str | Path,
        target_format: str = "mdx",
    ) -> DocFormatConvertResult:
        """Transpile Markdown, RST, or IPYNB into MDX with Svelte tags."""
        p = Path(source_path)
        content = (
            p.read_text(encoding="utf-8", errors="ignore")
            if p.exists()
            else str(source_path)
        )

        injected_components: list[str] = []

        # Convert Sphinx directives to Svelte components
        if ".. note::" in content or ".. warning::" in content or ".. tip::" in content:
            content = re.sub(
                r"\.\. note::\s*(.*?)(?=\n\S|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")
            content = re.sub(
                r"\.\. warning::\s*(.*?)(?=\n\S|\Z)",
                r"<Warning>\n\1\n</Warning>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Warning>")
            content = re.sub(
                r"\.\. tip::\s*(.*?)(?=\n\S|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")

        # Normalize markdown blockquotes: > [!NOTE] -> <Tip>
        if "> [!NOTE]" in content or "> [!TIP]" in content:
            content = re.sub(
                r"> \[!(?:NOTE|TIP)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
                r"<Tip>\n\1\n</Tip>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Tip>")
        if "> [!WARNING]" in content or "> [!CAUTION]" in content:
            content = re.sub(
                r"> \[!(?:WARNING|CAUTION)\]\s*\n?(.*?)(?=\n\s*\n|\Z)",
                r"<Warning>\n\1\n</Warning>",
                content,
                flags=re.DOTALL,
            )
            injected_components.append("<Warning>")

        return DocFormatConvertResult(
            source_path=str(p),
            target_format=target_format,
            converted_content=content,
            svelte_components_injected=tuple(sorted(set(injected_components))),
        )

    @staticmethod
    def lint_style(
        file_path: str | Path,
        fix: bool = False,
    ) -> DocLintResult:
        """Lint and format code examples inside docstrings or MDX files."""
        p = Path(file_path)
        content = (
            p.read_text(encoding="utf-8", errors="ignore")
            if p.exists()
            else str(file_path)
        )

        diagnostics: list[str] = []
        code_blocks = re.findall(r"```python(.*?)```", content, flags=re.DOTALL)
        for idx, block in enumerate(code_blocks, start=1):
            lines = block.strip().splitlines()
            if not lines:
                diagnostics.append(f"Block #{idx}: Empty python code block")
            for l_idx, line in enumerate(lines, start=1):
                if line.endswith((" ", "\t")):
                    diagnostics.append(
                        f"Block #{idx} Line {l_idx}: Trailing whitespace detected"
                    )

        formatted = content
        if fix:
            formatted = re.sub(
                r"```python(.*?)```",
                lambda m: (
                    "```python\n"
                    + "\n".join(l.rstrip() for l in m.group(1).strip().splitlines())
                    + "\n```"
                ),
                content,
                flags=re.DOTALL,
            )

        return DocLintResult(
            file_path=str(p),
            issues_count=len(diagnostics),
            diagnostics=tuple(diagnostics),
            formatted_content=formatted if fix else None,
        )

    @staticmethod
    def chunk_markdown(
        markdown_text: str,
        page_title: str = "Documentation",
        max_chunk_size: int = 1500,
    ) -> tuple[DocChunk, ...]:
        """Hierarchically partition Markdown text by headings for search indexing."""
        lines = markdown_text.splitlines()
        chunks: list[DocChunk] = []

        current_heading = page_title
        current_level = 1
        current_lines: list[str] = []
        heading_stack: list[str] = [page_title]
        chunk_idx = 0

        def flush_chunk() -> None:
            nonlocal chunk_idx, current_lines
            if not current_lines:
                return
            body = "\n".join(current_lines).strip()
            if body:
                chunks.append(
                    DocChunk(
                        chunk_id=f"chunk_{chunk_idx}",
                        title=current_heading,
                        heading_level=current_level,
                        content=body,
                        tokens_estimate=max(1, len(body) // 4),
                        breadcrumb=tuple(heading_stack),
                    )
                )
                chunk_idx += 1
            current_lines = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if header_match:
                flush_chunk()
                level = len(header_match.group(1))
                h_text = header_match.group(2).strip()

                while len(heading_stack) >= level and len(heading_stack) > 1:
                    heading_stack.pop()
                heading_stack.append(h_text)

                current_heading = h_text
                current_level = level
            else:
                current_lines.append(line)

        flush_chunk()

        if not chunks:
            chunks.append(
                DocChunk(
                    chunk_id="chunk_0",
                    title=page_title,
                    heading_level=1,
                    content=markdown_text[:max_chunk_size],
                    tokens_estimate=max(1, len(markdown_text[:max_chunk_size]) // 4),
                    breadcrumb=(page_title,),
                )
            )

        return tuple(chunks)


__all__ = [
    "DocBuilderDomainEngine",
]
