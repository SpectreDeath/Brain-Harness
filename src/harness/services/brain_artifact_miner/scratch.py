"""AST inspection and workspace scratch tool scanning (Rule 32, Rule 42, Rule 52)."""

from __future__ import annotations

import ast
import logging
import os
import sys
from pathlib import Path

from harness.services.brain_artifact_miner.models import (
    ScratchCatalog,
    ScratchCatalogItem,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger("harness.services.brain_artifact_miner.scratch")


def classify_script_ast(code: str, file_path: Path) -> tuple[str, list[str], list[str], str]:
    """Inspect a Python script via AST to extract metadata and category (Rule 42)."""
    tree = ast.parse(code, filename=str(file_path))
    docstring = ast.get_docstring(tree) or ""
    functions: list[str] = []
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    functions = list(dict.fromkeys(functions))
    imports = list(dict.fromkeys(imports))

    # Heuristic domain classification
    content_lower = (code + " " + " ".join(functions) + " " + " ".join(imports)).lower()
    fname = file_path.name.lower()

    if any(k in content_lower for k in ("ast.", "linter", "syntax", "brackets", "tokenize")) or "lint" in fname:
        category = "ast_and_lint"
    elif any(k in content_lower for k in ("sqlite3", "sql", "cursor", "select", "table", "wal")) or "db" in fname:
        category = "database_and_sql"
    elif (
        any(k in content_lower for k in ("html", "tailwind", "mermaid", "brief", "css", "svg"))
        or "brief" in fname
        or "visual" in fname
    ):
        category = "brief_and_visual"
    elif any(k in content_lower for k in ("pytest", "assert", "test_", "verification", "check_")):
        category = "test_and_verification"
    elif any(k in content_lower for k in ("search", "grep", "regex", "re.search", "find")):
        category = "inspection_and_search"
    elif any(k in content_lower for k in ("graph", "node", "edge", "dag", "bfs", "dfs", "tree")):
        category = "graph_and_topology"
    else:
        category = "domain_and_other"

    return category, functions, imports, docstring[:250]


def scan_scratch_tools(brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
    """Scan and catalog reusable Python scratch tools across conversation workspaces.

    Enforces:
    - Rule 52: Bounded directory traversal with noise pruning
    - Rule 32: Defensive batch visibility (never bare except: continue; reraise programming errors)
    - Rule 42: AST script hygiene and syntactic inspection
    """
    items_by_cat: dict[str, list[ScratchCatalogItem]] = {
        "ast_and_lint": [],
        "database_and_sql": [],
        "brief_and_visual": [],
        "test_and_verification": [],
        "inspection_and_search": [],
        "graph_and_topology": [],
        "domain_and_other": [],
    }

    if not brain_dir.exists():
        logger.warning("Brain directory does not exist: %s", brain_dir)
        return ScratchCatalog(total_scanned=0, classified_count=0, items_by_category=items_by_cat)

    total_scanned = 0
    classified_count = 0
    ignored_parts = {".git", "node_modules", ".venv", "__pycache__", "target", "dist", ".gemini"}

    for root, dirs, files in os.walk(brain_dir):
        # Prune noise directories in-place (Rule 52)
        dirs[:] = [d for d in dirs if d.lower() not in ignored_parts and not d.startswith(".")]

        rel_depth = len(Path(root).relative_to(brain_dir).parts)
        if rel_depth > max_depth:
            dirs.clear()
            continue

        if Path(root).name == "scratch":
            for f in files:
                if not f.endswith(".py"):
                    continue
                file_path = Path(root) / f
                total_scanned += 1

                try:
                    code = file_path.read_text(encoding="utf-8", errors="ignore")
                    category, funcs, imps, doc = classify_script_ast(code, file_path)
                    item = ScratchCatalogItem(
                        category=category,
                        path=str(file_path),
                        functions=funcs,
                        imports=imps,
                        docstring=doc,
                    )
                    items_by_cat.setdefault(category, []).append(item)
                    classified_count += 1
                except (NameError, TypeError, AttributeError) as prog_err:
                    # Explicitly reraise programming errors (Rule 32)
                    logger.error("Programming defect scanning %s: %s", file_path, prog_err)
                    raise
                except SyntaxError as syn_err:
                    logger.debug("Syntax error in scratch script %s: %s", file_path, syn_err)
                except Exception as ex:
                    # Log unexpected batch errors defensively (Rule 32)
                    logger.warning("Unexpected error inspecting scratch script %s: %s", file_path, ex)

    return ScratchCatalog(
        total_scanned=total_scanned,
        classified_count=classified_count,
        items_by_category=items_by_cat,
    )


__all__ = [
    "classify_script_ast",
    "scan_scratch_tools",
]
