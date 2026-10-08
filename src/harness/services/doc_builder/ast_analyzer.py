"""Static AST Parser & Table of Contents Auditor for doc_builder."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from harness.services.doc_builder.models import (
    AutodocParameter,
    AutodocSignature,
    TocDiagnostic,
)


class DocAstStaticAnalyzer:
    """Pure static AST analyzer extracting docstrings and signatures without execution."""

    @staticmethod
    def parse_source(
        source_text: str, target_object: str | None = None
    ) -> list[AutodocSignature]:
        tree = ast.parse(source_text)
        signatures: list[AutodocSignature] = []

        def _format_arg(
            arg: ast.arg, default: ast.expr | None = None
        ) -> AutodocParameter:
            ann = ast.unparse(arg.annotation) if arg.annotation else "Any"
            def_val = ast.unparse(default) if default else None
            return AutodocParameter(
                name=arg.arg,
                type_annotation=ann,
                default_value=def_val,
                description=f"Parameter {arg.arg}",
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if target_object and node.name != target_object:
                    continue
                doc = ast.get_docstring(node) or ""
                # Find __init__ method if available
                init_params: list[AutodocParameter] = []
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name == "__init__":
                        args = sub.args
                        defaults = [None] * (
                            len(args.args) - len(args.defaults)
                        ) + list(args.defaults)
                        for a, d in zip(args.args, defaults):
                            if a.arg != "self":
                                init_params.append(_format_arg(a, d))
                sig_str = f"{node.name}({', '.join(p.name for p in init_params)})"
                signatures.append(
                    AutodocSignature(
                        object_path=node.name,
                        signature_str=sig_str,
                        parameters=tuple(init_params),
                        return_type=node.name,
                        docstring=doc,
                        docstring_format="markdown",
                    )
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if target_object and node.name != target_object:
                    continue
                # Skip private helpers if not targeted
                if node.name.startswith("_") and not target_object:
                    continue
                doc = ast.get_docstring(node) or ""
                args = node.args
                defaults = [None] * (len(args.args) - len(args.defaults)) + list(
                    args.defaults
                )
                params: list[AutodocParameter] = []
                for a, d in zip(args.args, defaults):
                    if a.arg not in ("self", "cls"):
                        params.append(_format_arg(a, d))
                ret_ann = ast.unparse(node.returns) if node.returns else "None"
                sig_str = (
                    f"{node.name}({', '.join(p.name for p in params)}) -> {ret_ann}"
                )
                signatures.append(
                    AutodocSignature(
                        object_path=node.name,
                        signature_str=sig_str,
                        parameters=tuple(params),
                        return_type=ret_ann,
                        docstring=doc,
                        docstring_format="markdown",
                    )
                )

        return signatures


class TocIntegrityAuditor:
    """Audits _toctree.yml / _toctree.yaml against documentation files."""

    @staticmethod
    def audit_toc(docs_path: Path) -> tuple[tuple[TocDiagnostic, ...], tuple[str, ...]]:
        toc_files = [
            docs_path / "_toctree.yml",
            docs_path / "_toctree.yaml",
            docs_path / "_toctree.json",
        ]
        target_toc = next((f for f in toc_files if f.exists()), None)
        if not target_toc:
            return (), ()

        diagnostics: list[TocDiagnostic] = []
        indexed_pages: set[str] = set()

        raw_text = target_toc.read_text(encoding="utf-8", errors="ignore")
        # Try YAML parsing or fallback regex extraction
        entries: list[str] = []
        try:
            import yaml

            parsed = yaml.safe_load(raw_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        if "local" in item:
                            entries.append(str(item["local"]))
                        elif "sections" in item and isinstance(item["sections"], list):
                            for sub in item["sections"]:
                                if isinstance(sub, dict) and "local" in sub:
                                    entries.append(str(sub["local"]))
                    elif isinstance(item, str):
                        entries.append(item)
        except Exception:
            # Fallback regex search for 'local: <path>' or simple entries
            for m in re.finditer(r"local:\s*([^\s#]+)", raw_text):
                entries.append(m.group(1).strip("'\""))

        for entry in entries:
            clean_entry = entry.strip().lstrip("/")
            possible_files = [
                docs_path / clean_entry,
                docs_path / f"{clean_entry}.md",
                docs_path / f"{clean_entry}.mdx",
                docs_path / clean_entry / "index.md",
            ]
            matched = next((p for p in possible_files if p.exists()), None)
            if matched:
                rel = str(matched.relative_to(docs_path)).replace("\\", "/")
                indexed_pages.add(rel)
                # also add extensionless
                indexed_pages.add(rel.rsplit(".", 1)[0])
                diagnostics.append(
                    TocDiagnostic(entry=entry, file_path=rel, is_valid=True)
                )
            else:
                diagnostics.append(
                    TocDiagnostic(
                        entry=entry,
                        file_path=None,
                        is_valid=False,
                        error_reason=f"TOC entry '{entry}' does not resolve to an existing file in {docs_path}",
                    )
                )

        # Detect orphaned markdown/mdx documentation files
        all_md_files = list(docs_path.rglob("*.md")) + list(docs_path.rglob("*.mdx"))
        orphans: list[str] = []
        for mf in all_md_files:
            rel = str(mf.relative_to(docs_path)).replace("\\", "/")
            base_rel = rel.rsplit(".", 1)[0]
            if (
                rel not in indexed_pages
                and base_rel not in indexed_pages
                and not rel.startswith("_")
            ):
                orphans.append(rel)

        return tuple(diagnostics), tuple(sorted(orphans))


__all__ = [
    "DocAstStaticAnalyzer",
    "TocIntegrityAuditor",
]
