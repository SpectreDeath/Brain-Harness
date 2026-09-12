# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
Repository Documentation Synchronizer & Coverage Engine.

Inspects codebases via AST, calculates documentation coverage, detects documentation drift,
and scaffolds standardized Diátaxis documentation suites.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Co-located import
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from doc_ast_inspector import (
    inspect_module_ast,
)

# ---------------------------------------------------------------------------
# Rule 12: Slotted & Frozen Domain Dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ModuleDocStatus:
    """Documentation coverage status for a single Python module."""

    module_path: str
    module_name: str
    has_module_docstring: bool
    total_symbols: int
    documented_symbols: int
    dedicated_doc_path: str | None
    coverage_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "has_module_docstring": self.has_module_docstring,
            "total_symbols": self.total_symbols,
            "documented_symbols": self.documented_symbols,
            "dedicated_doc_path": self.dedicated_doc_path,
            "coverage_pct": round(self.coverage_pct, 1),
        }


@dataclass(slots=True, frozen=True)
class DocCoverageReport:
    """Aggregate documentation coverage report across a repository or directory."""

    scanned_root: str
    total_modules: int
    modules_with_docstring: int
    total_symbols: int
    documented_symbols: int
    overall_coverage_pct: float
    min_passing_score: float
    passed: bool
    missing_docs: tuple[str, ...]
    modules: tuple[ModuleDocStatus, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_root": self.scanned_root,
            "total_modules": self.total_modules,
            "modules_with_docstring": self.modules_with_docstring,
            "total_symbols": self.total_symbols,
            "documented_symbols": self.documented_symbols,
            "overall_coverage_pct": round(self.overall_coverage_pct, 1),
            "min_passing_score": self.min_passing_score,
            "passed": self.passed,
            "missing_docs_count": len(self.missing_docs),
            "missing_docs": list(self.missing_docs),
            "modules": [m.to_dict() for m in self.modules],
        }


@dataclass(slots=True, frozen=True)
class BrokenLink:
    """Detected broken relative file link inside documentation."""

    source_file: str
    target_link: str
    line_number: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "target_link": self.target_link,
            "line_number": self.line_number,
            "reason": self.reason,
        }


@dataclass(slots=True, frozen=True)
class StaleSymbol:
    """Detected stale or non-existent symbol reference inside documentation."""

    source_file: str
    symbol_name: str
    line_number: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "symbol_name": self.symbol_name,
            "line_number": self.line_number,
            "reason": self.reason,
        }


@dataclass(slots=True, frozen=True)
class DocDriftReport:
    """Report on documentation drift, broken references, and stale symbols."""

    scanned_docs_count: int
    broken_links: tuple[BrokenLink, ...]
    stale_symbols: tuple[StaleSymbol, ...]
    has_drift: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned_docs_count": self.scanned_docs_count,
            "broken_links_count": len(self.broken_links),
            "broken_links": [b.to_dict() for b in self.broken_links],
            "stale_symbols_count": len(self.stale_symbols),
            "stale_symbols": [
                s.to_dict() if hasattr(s, "to_dict") else str(s)
                for s in self.stale_symbols
            ],
            "has_drift": self.has_drift,
        }


# ---------------------------------------------------------------------------
# Core Synchronizer Engine
# ---------------------------------------------------------------------------


class DocSynchronizerEngine:
    """Engine executing AST audits, drift detection, and Diátaxis scaffolding."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        self.root_dir = Path(root_dir or ".").resolve()
        self.templates_dir = Path(__file__).resolve().parent.parent / "templates"
        self._config = self._load_config()
        self._ast_cache: dict[str, tuple[float, Any]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    @property
    def cache_stats(self) -> dict[str, int]:
        """Return AST inspection cache statistics."""
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "cached_entries": len(self._ast_cache),
        }

    def _inspect_cached(self, f: Path) -> Any | None:
        """Inspect module AST with mtime-indexed in-memory caching."""
        try:
            mtime = f.stat().st_mtime
        except OSError:
            return None
        cached = self._ast_cache.get(str(f))
        if cached is not None and cached[0] == mtime:
            self._cache_hits += 1
            return cached[1]
        insp = inspect_module_ast(f)
        if insp is not None:
            self._cache_misses += 1
            self._ast_cache[str(f)] = (mtime, insp)
        return insp

    def _load_config(self) -> dict[str, Any]:
        cfg_file = Path(__file__).resolve().parent.parent / "config.default.yaml"
        if cfg_file.exists() and yaml is not None:
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {
            "audit": {
                "min_coverage_pct": 80.0,
                "exclude_patterns": [
                    ".git",
                    ".pytest_cache",
                    ".venv",
                    "venv",
                    "__pycache__",
                    "build",
                    "dist",
                ],
            }
        }

    def audit(
        self,
        target_dir: Path | str | None = None,
        min_coverage: float = 80.0,
        exclude_patterns: list[str] | None = None,
    ) -> DocCoverageReport:
        """Audits all Python modules in target_dir against existing Markdown docs."""
        scan_dir = Path(target_dir or self.root_dir).resolve()
        excludes = exclude_patterns or self._config.get("audit", {}).get(
            "exclude_patterns", []
        )

        # Gather all python files
        py_files: list[Path] = []
        for p in scan_dir.rglob("*.py"):
            parts = p.parts
            if any(ex in parts for ex in excludes):
                continue
            if p.name.startswith("test_") or "tests" in parts:
                continue
            py_files.append(p)

        # Gather all markdown files in repo to map dedicated docs
        md_files = list(self.root_dir.rglob("*.md"))
        md_names = {m.stem.lower(): m for m in md_files}

        module_statuses: list[ModuleDocStatus] = []
        missing_docs: list[str] = []

        total_symbols_all = 0
        doc_symbols_all = 0
        modules_with_docstring = 0

        for f in py_files:
            insp = self._inspect_cached(f)
            if not insp:
                continue

            # Calculate symbol-level docstring coverage
            sym_total = insp.total_public_symbols
            doc_count = 0

            for c in insp.classes:
                if c.docstring and c.docstring.strip():
                    doc_count += 1
                for m in c.methods:
                    if m.docstring and m.docstring.strip():
                        doc_count += 1

            for fn in insp.functions:
                if fn.docstring and fn.docstring.strip():
                    doc_count += 1

            # Check if dedicated markdown doc exists
            mod_stem = f.stem.lower()
            dedicated_doc: str | None = None

            # 1. Sibling README or doc
            sibling_readme = f.parent / "README.md"
            sibling_doc = f.with_suffix(".md")
            if sibling_readme.exists():
                try:
                    dedicated_doc = str(
                        sibling_readme.relative_to(self.root_dir)
                    ).replace("\\", "/")
                except ValueError:
                    dedicated_doc = str(sibling_readme.relative_to(scan_dir)).replace(
                        "\\", "/"
                    )
            elif sibling_doc.exists():
                try:
                    dedicated_doc = str(sibling_doc.relative_to(self.root_dir)).replace(
                        "\\", "/"
                    )
                except ValueError:
                    dedicated_doc = str(sibling_doc.relative_to(scan_dir)).replace(
                        "\\", "/"
                    )
            elif mod_stem in md_names:
                try:
                    dedicated_doc = str(
                        md_names[mod_stem].relative_to(self.root_dir)
                    ).replace("\\", "/")
                except ValueError:
                    dedicated_doc = str(
                        md_names[mod_stem].relative_to(scan_dir)
                    ).replace("\\", "/")

            total_symbols_all += sym_total
            doc_symbols_all += doc_count
            if insp.has_module_docstring:
                modules_with_docstring += 1

            # Weighting: 40% module docstring, 30% symbol docstrings, 30% dedicated markdown doc
            mod_score = 40.0 if insp.has_module_docstring else 0.0
            sym_score = (doc_count / max(1, sym_total)) * 30.0
            doc_score = 30.0 if dedicated_doc else 0.0
            coverage_pct = min(100.0, mod_score + sym_score + doc_score)

            try:
                rel_f = str(f.relative_to(self.root_dir)).replace("\\", "/")
            except ValueError:
                rel_f = str(f.relative_to(scan_dir)).replace("\\", "/")
            status = ModuleDocStatus(
                module_path=rel_f,
                module_name=insp.module_name,
                has_module_docstring=insp.has_module_docstring,
                total_symbols=sym_total,
                documented_symbols=doc_count,
                dedicated_doc_path=dedicated_doc,
                coverage_pct=coverage_pct,
            )
            module_statuses.append(status)

            if coverage_pct < min_coverage or not dedicated_doc:
                missing_docs.append(rel_f)

        total_mods = len(module_statuses)
        if total_mods == 0:
            return DocCoverageReport(
                scanned_root=str(scan_dir).replace("\\", "/"),
                total_modules=0,
                modules_with_docstring=0,
                total_symbols=0,
                documented_symbols=0,
                overall_coverage_pct=100.0,
                min_passing_score=min_coverage,
                passed=True,
                missing_docs=(),
                modules=(),
            )

        overall_pct = sum(m.coverage_pct for m in module_statuses) / total_mods
        passed = overall_pct >= min_coverage

        return DocCoverageReport(
            scanned_root=str(scan_dir).replace("\\", "/"),
            total_modules=total_mods,
            modules_with_docstring=modules_with_docstring,
            total_symbols=total_symbols_all,
            documented_symbols=doc_symbols_all,
            overall_coverage_pct=overall_pct,
            min_passing_score=min_coverage,
            passed=passed,
            missing_docs=tuple(missing_docs),
            modules=tuple(module_statuses),
        )

    def drift_check(
        self,
        docs_dir: Path | str | None = None,
        check_symbols: bool = True,
    ) -> DocDriftReport:
        """Inspects markdown documents for broken relative links and stale AST symbol references."""
        d_path = Path(docs_dir or self.root_dir).resolve()
        md_files = list(d_path.rglob("*.md"))

        broken_links: list[BrokenLink] = []
        stale_symbols: list[StaleSymbol] = []
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        explicit_class_pattern = re.compile(r"`class\s+([A-Za-z0-9_]+)`")
        explicit_func_pattern = re.compile(r"`def\s+([A-Za-z0-9_]+)(?:\([^`]*\))?`")
        method_call_pattern = re.compile(r"`([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)(?:\(\))?`")

        scanned_count = 0
        for md in md_files:
            # Skip ignored directories
            if any(
                ex in md.parts
                for ex in [
                    ".git",
                    ".pytest_cache",
                    ".venv",
                    "venv",
                    "node_modules",
                    "scratch",
                    ".system_generated",
                    "test_ingested_plugins",
                    ".harness",
                ]
            ):
                continue

            scanned_count += 1
            try:
                content = md.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.debug("skip_unreadable_doc", file=str(md), error=str(e))
                continue

            try:
                rel_source = str(md.relative_to(self.root_dir)).replace("\\", "/")
            except ValueError:
                rel_source = str(md.relative_to(d_path)).replace("\\", "/")

            # Strip code blocks to avoid false positives (Rule 47)
            clean_content = re.sub(r"(?s)```.*?```", "", content)
            lines = clean_content.splitlines()

            # Track referenced Python modules in this doc
            associated_py_files: set[Path] = set()

            for line_idx, line in enumerate(lines, 1):
                # Isolate inline backtick expressions that are not link text (Rule 47)
                line_no_backticks = re.sub(r"(?<!\[)`([^`]+)`(?!\])", "", line)
                for match in link_pattern.finditer(line_no_backticks):
                    target = match.group(2).strip()

                    # Skip anchors, mailto, http URLs, and Python quoted strings
                    if target.startswith(("#", "http://", "https://", "mailto:", '"', "'")):
                        continue

                    # Clean target of #anchor queries
                    clean_target = target.split("#")[0].split("?")[0].strip("\"'")
                    if not clean_target:
                        continue

                    # Handle file:/// URIs per Rule 47
                    if clean_target.startswith("file://"):
                        from urllib.parse import unquote, urlparse

                        parsed_uri = urlparse(clean_target)
                        uri_path = unquote(parsed_uri.path)
                        if (
                            sys.platform == "win32"
                            and uri_path.startswith("/")
                            and len(uri_path) > 2
                            and uri_path[2] == ":"
                        ):
                            uri_path = uri_path[1:]

                        file_p = Path(uri_path)
                        if file_p.exists():
                            try:
                                rel_within = file_p.relative_to(self.root_dir)
                                broken_links.append(
                                    BrokenLink(
                                        source_file=rel_source,
                                        target_link=target,
                                        line_number=line_idx,
                                        reason=f"Rule 47 violation: absolute file URI used for workspace path (use relative path: {rel_within.as_posix()})",
                                    )
                                )
                            except ValueError:
                                pass  # External file exists
                        else:
                            broken_links.append(
                                BrokenLink(
                                    source_file=rel_source,
                                    target_link=target,
                                    line_number=line_idx,
                                    reason=f"Target file does not exist on filesystem: {uri_path}",
                                )
                            )
                        continue

                    # Resolve link relative to the markdown file's directory
                    resolved_target = (md.parent / clean_target).resolve()
                    if not resolved_target.exists():
                        broken_links.append(
                            BrokenLink(
                                source_file=rel_source,
                                target_link=target,
                                line_number=line_idx,
                                reason="Target file does not exist on filesystem",
                            )
                        )
                    elif resolved_target.suffix == ".py":
                        associated_py_files.add(resolved_target)

            # Map implicit associated modules
            if md.name.endswith("_api.md"):
                stem_base = md.name[:-7]
                for candidate in self.root_dir.rglob(f"{stem_base}.py"):
                    if candidate.exists() and "tests" not in candidate.parts:
                        associated_py_files.add(candidate)
            elif md.with_suffix(".py").exists():
                associated_py_files.add(md.with_suffix(".py"))
            elif md.name.lower() in ("readme.md", "index.md"):
                for p in md.parent.glob("*.py"):
                    if not p.name.startswith("test_"):
                        associated_py_files.add(p)

            # Code-to-Doc Symbol Drift Verification
            if check_symbols and associated_py_files:
                valid_classes: set[str] = set()
                valid_methods: set[str] = set()
                valid_functions: set[str] = set()
                class_to_methods: dict[str, set[str]] = {}

                for py_f in associated_py_files:
                    insp = self._inspect_cached(py_f)
                    if insp:
                        for c in insp.classes:
                            valid_classes.add(c.name)
                            m_set = {m.name for m in c.methods}
                            valid_methods.update(m_set)
                            class_to_methods[c.name] = m_set
                        for fn in insp.functions:
                            valid_functions.add(fn.name)

                common_allowed = {
                    "__init__",
                    "__repr__",
                    "__str__",
                    "__enter__",
                    "__exit__",
                    "main",
                    "setUp",
                    "tearDown",
                    "self",
                    "args",
                    "kwargs",
                }
                py_refs_list = []
                for p in associated_py_files:
                    try:
                        py_refs_list.append(
                            str(p.relative_to(self.root_dir)).replace("\\", "/")
                        )
                    except ValueError:
                        py_refs_list.append(
                            str(p.relative_to(d_path)).replace("\\", "/")
                        )
                py_refs_str = ", ".join(py_refs_list)

                for line_idx, line in enumerate(lines, 1):
                    # 1. Explicit `class Symbol`
                    for m in explicit_class_pattern.finditer(line):
                        cls_name = m.group(1)
                        if cls_name not in valid_classes:
                            stale_symbols.append(
                                StaleSymbol(
                                    source_file=rel_source,
                                    symbol_name=cls_name,
                                    line_number=line_idx,
                                    reason=f"Class '{cls_name}' not found in referenced module(s) ({py_refs_str})",
                                )
                            )

                    # 2. Explicit `def symbol(...)`
                    for m in explicit_func_pattern.finditer(line):
                        func_name = m.group(1)
                        if (
                            func_name not in valid_methods
                            and func_name not in valid_functions
                            and func_name not in common_allowed
                        ):
                            stale_symbols.append(
                                StaleSymbol(
                                    source_file=rel_source,
                                    symbol_name=func_name,
                                    line_number=line_idx,
                                    reason=f"Function or method '{func_name}' not found in referenced module(s) ({py_refs_str})",
                                )
                            )

                    # 3. Qualified method calls: `Class.method()`
                    for m in method_call_pattern.finditer(line):
                        cls_or_mod, member = m.group(1), m.group(2)
                        if (
                            cls_or_mod in class_to_methods
                            and member not in class_to_methods[cls_or_mod]
                            and member not in common_allowed
                        ):
                            stale_symbols.append(
                                StaleSymbol(
                                    source_file=rel_source,
                                    symbol_name=f"{cls_or_mod}.{member}",
                                    line_number=line_idx,
                                    reason=f"Method '{member}' not found on class '{cls_or_mod}' in ({py_refs_str})",
                                )
                            )

        has_drift = len(broken_links) > 0 or len(stale_symbols) > 0
        return DocDriftReport(
            scanned_docs_count=scanned_count,
            broken_links=tuple(broken_links),
            stale_symbols=tuple(stale_symbols),
            has_drift=has_drift,
        )

    def scaffold(
        self,
        module_path: Path | str,
        doc_type: str = "api",
        output_path: Path | str | None = None,
    ) -> Path:
        """Scaffolds standardized Diátaxis documentation using live AST symbols."""
        m_file = Path(module_path).resolve()
        insp = inspect_module_ast(m_file)
        if not insp:
            raise FileNotFoundError(f"Could not inspect Python module: {module_path}")

        tpl_name = "api_reference.md.template"
        if doc_type == "readme":
            tpl_name = "package_readme.md.template"
        elif doc_type == "howto":
            tpl_name = "howto_guide.md.template"

        tpl_file = self.templates_dir / tpl_name
        template_text = tpl_file.read_text(encoding="utf-8")

        # Format sections
        classes_sec = []
        for c in insp.classes:
            classes_sec.append(f"### `class {c.name}`\n")
            if c.docstring:
                classes_sec.append(f"{c.docstring.strip()}\n")
            if c.methods:
                classes_sec.append("**Methods**:")
                for m in c.methods:
                    args_str = ", ".join(m.args)
                    ret_str = (
                        f" -> {m.return_annotation}" if m.return_annotation else ""
                    )
                    doc_brief = (
                        f" — {m.docstring.splitlines()[0]}" if m.docstring else ""
                    )
                    classes_sec.append(
                        f"- `def {m.name}({args_str}){ret_str}`{doc_brief}"
                    )
            classes_sec.append("\n")

        functions_sec = []
        for fn in insp.functions:
            args_str = ", ".join(fn.args)
            ret_str = f" -> {fn.return_annotation}" if fn.return_annotation else ""
            functions_sec.append(f"### `def {fn.name}({args_str}){ret_str}`\n")
            if fn.docstring:
                functions_sec.append(f"{fn.docstring.strip()}\n")
            functions_sec.append("\n")

        rendered = template_text.format(
            module_name=insp.module_name,
            package_name=insp.module_name,
            module_path=insp.file_path,
            class_count=len(insp.classes),
            function_count=len(insp.functions),
            module_docstring=insp.docstring or "Documentation for this module.",
            package_summary=insp.docstring or f"Core module {insp.module_name}.",
            package_purpose="domain capabilities and core logic",
            architecture_notes="Slotted domain architecture ensuring high-leverage execution.",
            symbol_table="| Symbol | Type |\n|---|---|\n"
            + "\n".join(f"| `{c.name}` | Class |" for c in insp.classes),
            quickstart_example=f"from {insp.module_name} import {insp.classes[0].name if insp.classes else '...'}",
            classes_section="\n".join(classes_sec)
            if classes_sec
            else "_No public classes defined._",
            functions_section="\n".join(functions_sec)
            if functions_sec
            else "_No top-level public functions defined._",
            errors_section="This module uses standard exceptions with actionable error payloads.",
            guide_title=f"Using {insp.module_name}",
            problem_statement=f"How to utilize {insp.module_name} in workflows.",
            dependencies="Python >= 3.10",
            step_1_title=f"Import {insp.module_name}",
            step_1_body="Import the primary classes or functions.",
            step_1_code=f"import {insp.module_name}",
            step_2_title="Invoke core method",
            step_2_body="Execute the primary domain capability.",
            step_2_code="# Call module function or class method",
            verification_instructions="Assert return status and inspect results.",
        )

        out_file = Path(output_path) if output_path else m_file.with_suffix(".md")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(rendered, encoding="utf-8")
        return out_file

    def visual_brief(
        self,
        target_dir: Path | str | None = None,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generates an interactive HTML visual brief with Mermaid topology diagrams."""
        report = self.audit(target_dir=target_dir)
        now_str = datetime.now(timezone.utc).isoformat()

        # Build Mermaid flowchart nodes
        mermaid_nodes = []
        for idx, m in enumerate(report.modules[:30]):
            node_id = f"m_{idx}"
            color_class = "covered" if m.coverage_pct >= 80.0 else "missing"
            clean_name = m.module_name.replace("-", "_")
            mermaid_nodes.append(
                f'    {node_id}["{clean_name} ({m.coverage_pct:.0f}%)"]:::{color_class}'
            )

        mermaid_code = "graph TD\n" + "\n".join(mermaid_nodes)
        mermaid_code += "\n    classDef covered fill:#238636,stroke:#2ea043,color:#fff;"
        mermaid_code += "\n    classDef missing fill:#da3633,stroke:#f85149,color:#fff;"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Documentation Coverage Brief & Scorecard</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --accent: #58a6ff;
      --text: #c9d1d9;
      --heading: #f0f6fc;
      --success: #3fb950;
      --danger: #f85149;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    h1, h2, h3 {{ color: var(--heading); }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 14px;
    }}
    .badge-pass {{ background: rgba(63, 185, 80, 0.2); color: var(--success); border: 1px solid var(--success); }}
    .badge-fail {{ background: rgba(248, 81, 73, 0.2); color: var(--danger); border: 1px solid var(--danger); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid var(--border); font-size: 14px; }}
    th {{ color: var(--heading); background: rgba(255, 255, 255, 0.02); }}
    .mermaid {{ margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Documentation Coverage Brief & Scorecard</h1>
    <p>Generated at: <code>{now_str}</code> | Root: <code>{report.scanned_root}</code></p>

    <div class="card">
      <h2>Overall Coverage Score</h2>
      <p>
        <span class="badge {"badge-pass" if report.passed else "badge-fail"}">
          {"✓ PASSED" if report.passed else "✗ COVERAGE DEFICIT"} ({report.overall_coverage_pct:.1f}%)
        </span>
        Target Threshold: <strong>{report.min_passing_score:.1f}%</strong>
      </p>
      <ul>
        <li>Total Scanned Modules: <strong>{report.total_modules}</strong></li>
        <li>Modules with Docstrings: <strong>{report.modules_with_docstring}</strong></li>
        <li>Total Public Symbols: <strong>{report.total_symbols}</strong></li>
        <li>Documented Symbols: <strong>{report.documented_symbols}</strong></li>
        <li>Missing or Stale Documentation: <strong>{len(report.missing_docs)}</strong></li>
      </ul>
    </div>

    <div class="card">
      <h2>Module Documentation Topology</h2>
      <div class="mermaid">
{mermaid_code}
      </div>
    </div>

    <div class="card">
      <h2>Module Detail Breakdown</h2>
      <table>
        <thead>
          <tr>
            <th>Module</th>
            <th>Docstring</th>
            <th>Symbols</th>
            <th>Dedicated Doc</th>
            <th>Coverage</th>
          </tr>
        </thead>
        <tbody>
"""
        for m in report.modules:
            doc_badge = "✓ Yes" if m.has_module_docstring else "✗ No"
            ded_badge = (
                f"<code>{m.dedicated_doc_path}</code>"
                if m.dedicated_doc_path
                else "<em>None</em>"
            )
            html += f"""          <tr>
            <td><code>{m.module_path}</code></td>
            <td>{doc_badge}</td>
            <td>{m.documented_symbols} / {m.total_symbols}</td>
            <td>{ded_badge}</td>
            <td><strong>{m.coverage_pct:.1f}%</strong></td>
          </tr>\n"""

        html += """        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
        out_p = (
            Path(output_path)
            if output_path
            else Path(os.environ.get("TEMP", "."))
            / f"doc_coverage_brief_{int(datetime.now(timezone.utc).timestamp())}.html"
        )
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(html, encoding="utf-8")
        return out_p


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def cmd_audit(args: argparse.Namespace) -> int:
    """Executes documentation coverage audit."""
    engine = DocSynchronizerEngine(root_dir=args.root)
    report = engine.audit(target_dir=args.target, min_coverage=args.min_coverage)

    out_p = Path(args.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    status_str = "PASS" if report.passed else "DEFICIT"
    print(
        f"Success! Audit [{status_str} | {report.overall_coverage_pct:.1f}% coverage]. "
        f"Missing docs: {len(report.missing_docs)}. Written to: {out_p}"
    )
    return 0 if report.passed else 1


def cmd_drift_check(args: argparse.Namespace) -> int:
    """Executes documentation link and symbol drift inspection."""
    engine = DocSynchronizerEngine(root_dir=args.root)
    check_syms = getattr(args, "check_symbols", True)
    report = engine.drift_check(docs_dir=args.docs_dir, check_symbols=check_syms)

    out_p = Path(args.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    status_str = "CLEAN" if not report.has_drift else "DRIFT DETECTED"
    print(
        f"Success! Drift Check [{status_str} | {len(report.broken_links)} broken links | {len(report.stale_symbols)} stale symbols]. Written to: {out_p}"
    )
    return 0 if not report.has_drift else 1


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Scaffolds Diátaxis documentation for a module."""
    engine = DocSynchronizerEngine(root_dir=args.root)
    try:
        out_p = engine.scaffold(
            module_path=args.module,
            doc_type=args.type,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error scaffolding documentation: {e}", file=sys.stderr)
        return 1

    print(
        f"Success! Scaffolded {args.type} documentation for {args.module}. Written to: {out_p}"
    )
    return 0


def cmd_visual_brief(args: argparse.Namespace) -> int:
    """Generates an interactive HTML visual brief with Mermaid topology."""
    engine = DocSynchronizerEngine(root_dir=args.root)
    out_p = engine.visual_brief(target_dir=args.target, output_path=args.output)
    print(f"Success! Visual brief generated. Written to: {out_p}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--root", default=".", help="Repository root directory")

    parser = argparse.ArgumentParser(
        description="Repository Documentation Synchronizer & Coverage Engine",
        parents=[common_parser],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit
    p_audit = subparsers.add_parser(
        "audit",
        parents=[common_parser],
        help="Audit documentation coverage against live AST symbols",
    )
    p_audit.add_argument("--target", help="Specific subdirectory to scan")
    p_audit.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum passing coverage percentage",
    )
    p_audit.add_argument("--output", required=True, help="Output JSON filepath")
    p_audit.set_defaults(func=cmd_audit)

    # drift-check
    p_drift = subparsers.add_parser(
        "drift-check",
        parents=[common_parser],
        help="Check markdown documents for broken links or stale symbols",
    )
    p_drift.add_argument(
        "--docs-dir", help="Directory containing markdown documentation"
    )
    p_drift.add_argument(
        "--check-symbols",
        action="store_true",
        default=True,
        help="Verify code symbol references against live AST",
    )
    p_drift.add_argument(
        "--no-symbols",
        action="store_false",
        dest="check_symbols",
        help="Skip AST symbol checking and only verify relative links",
    )
    p_drift.add_argument("--output", required=True, help="Output JSON filepath")
    p_drift.set_defaults(func=cmd_drift_check)

    # scaffold
    p_scaffold = subparsers.add_parser(
        "scaffold",
        parents=[common_parser],
        help="Scaffold standardized Diátaxis documentation",
    )
    p_scaffold.add_argument(
        "--module", required=True, help="Path to target Python module"
    )
    p_scaffold.add_argument(
        "--type",
        choices=["api", "readme", "howto"],
        default="api",
        help="Diátaxis document type",
    )
    p_scaffold.add_argument("--output", required=True, help="Output Markdown filepath")
    p_scaffold.set_defaults(func=cmd_scaffold)

    # visual-brief
    p_brief = subparsers.add_parser(
        "visual-brief",
        parents=[common_parser],
        help="Generate interactive HTML visual brief with Mermaid diagram",
    )
    p_brief.add_argument("--target", help="Specific subdirectory to scan")
    p_brief.add_argument("--output", help="Output HTML filepath")
    p_brief.set_defaults(func=cmd_visual_brief)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
