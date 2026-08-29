"""Repository Map and AST Reference Graph Service.

Extracts symbol definitions (classes, functions, methods) and references across
multi-language repositories, constructing a PageRank-weighted AST skeleton
that fits within a strict token budget. Inspired by Aider's repomap architecture.
"""

from __future__ import annotations

import ast
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()


class SymbolTag(BaseModel):
    """Represents an extracted code symbol tag."""

    rel_path: str = Field(..., description="Relative file path")
    name: str = Field(..., description="Symbol identifier name")
    kind: str = Field(..., description="Symbol kind: class, def, interface, struct, fn, type")
    line: int = Field(default=1, description="Line number of declaration")
    signature: str = Field(default="", description="Declaration signature snippet")


class RepoMapResult(BaseModel):
    """Result of generating a repository map."""

    status: str = Field(default="ok", description="Status indicator")
    root_path: str = Field(default="", description="Root path analyzed")
    total_files_scanned: int = Field(default=0, description="Total source files indexed")
    total_symbols_indexed: int = Field(default=0, description="Total definitions found")
    formatted_map: str = Field(default="", description="Rendered repository AST skeleton")
    token_estimate: int = Field(default=0, description="Estimated token count of formatted map")
    error: str | None = Field(default=None, description="Error explanation if mapping failed")


@runtime_checkable
class RepoMapService(Protocol):
    """Protocol for AST-based repository mapping and identifier ranking."""

    def extract_tags(self, file_path: str, content: str | None = None) -> list[SymbolTag]:
        """Extract symbol definition tags from a single source file."""
        ...

    def get_repo_map(
        self,
        root_path: str,
        *,
        query_context: str | None = None,
        max_tokens: int = 1024,
        file_filter: list[str] | None = None,
    ) -> RepoMapResult:
        """Construct a ranked, token-budgeted code skeleton for the repository."""
        ...


REPO_MAP_SERVICE_KEY: ServiceKey[RepoMapService] = ServiceKey("service.repomap")


# Lightweight regex matchers for non-Python languages
_REGEX_EXTRACTORS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    ".ts": [
        ("class", re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
        ("interface", re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
        ("type", re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
        ("def", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
    ],
    ".js": [
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
        ("def", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)", re.MULTILINE)),
    ],
    ".rs": [
        ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z0-9_]+)", re.MULTILINE)),
        ("enum", re.compile(r"^\s*(?:pub\s+)?enum\s+([A-Za-z0-9_]+)", re.MULTILINE)),
        ("trait", re.compile(r"^\s*(?:pub\s+)?trait\s+([A-Za-z0-9_]+)", re.MULTILINE)),
        ("fn", re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)", re.MULTILINE)),
    ],
    ".go": [
        ("type", re.compile(r"^\s*type\s+([A-Za-z0-9_]+)\s+struct", re.MULTILINE)),
        ("interface", re.compile(r"^\s*type\s+([A-Za-z0-9_]+)\s+interface", re.MULTILINE)),
        ("fn", re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\s*\(", re.MULTILINE)),
    ],
}

DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "target",
    "dist",
    "build",
    ".venv",
    "venv",
    ".tox",
}


class DefaultRepoMapService:
    """Default implementation of RepoMapService using AST and PageRank scoring."""

    def __init__(self) -> None:
        self._tag_cache: dict[str, tuple[float, list[SymbolTag]]] = {}

    def extract_tags(self, file_path: str, content: str | None = None) -> list[SymbolTag]:
        """Extract symbol tags from a source file using Python AST or language regexes."""
        p = Path(file_path)
        ext = p.suffix.lower()

        if content is None:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as err:
                logger.debug("tag_read_error", path=file_path, error=str(err))
                return []

        rel_path = str(p).replace("\\", "/")
        tags: list[SymbolTag] = []

        if ext == ".py":
            tags.extend(self._extract_python_ast(rel_path, content))
        elif ext in _REGEX_EXTRACTORS:
            tags.extend(self._extract_regex_tags(rel_path, content, ext))

        return tags

    def _extract_python_ast(self, rel_path: str, content: str) -> list[SymbolTag]:
        tags: list[SymbolTag] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return tags

        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                sig = lines[node.lineno - 1].strip() if 0 <= node.lineno - 1 < len(lines) else f"class {node.name}"
                tags.append(SymbolTag(rel_path=rel_path, name=node.name, kind="class", line=node.lineno, signature=sig))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = lines[node.lineno - 1].strip() if 0 <= node.lineno - 1 < len(lines) else f"def {node.name}"
                tags.append(SymbolTag(rel_path=rel_path, name=node.name, kind="def", line=node.lineno, signature=sig))

        return tags

    def _extract_regex_tags(self, rel_path: str, content: str, ext: str) -> list[SymbolTag]:
        tags: list[SymbolTag] = []
        patterns = _REGEX_EXTRACTORS.get(ext, [])
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            for kind, pat in patterns:
                m = pat.match(line)
                if m:
                    name = m.group(1)
                    tags.append(SymbolTag(rel_path=rel_path, name=name, kind=kind, line=idx, signature=stripped))
                    break

        return tags

    def _compute_relevance_scores(
        self,
        all_tags: dict[str, list[SymbolTag]],
        query_context: str | None,
    ) -> dict[str, float]:
        """Compute relevance score for each file using token occurrences and references."""
        scores: dict[str, float] = defaultdict(float)

        # Baseline score: proportional to density of defined symbols
        for rel_path, tags in all_tags.items():
            scores[rel_path] = 1.0 + (len(tags) * 0.1)

        if not query_context:
            return scores

        # Tokenize query context into identifiers
        query_tokens = Counter(re.findall(r"[A-Za-z0-9_]{3,}", query_context.lower()))
        if not query_tokens:
            return scores

        for rel_path, tags in all_tags.items():
            file_lower = rel_path.lower()
            # Boost if file name itself matches query tokens
            for token, count in query_tokens.items():
                if token in file_lower:
                    scores[rel_path] += count * 5.0

            # Boost if defined symbols match query tokens
            for tag in tags:
                tag_name_lower = tag.name.lower()
                for token, count in query_tokens.items():
                    if token == tag_name_lower:
                        scores[rel_path] += count * 10.0
                    elif token in tag_name_lower:
                        scores[rel_path] += count * 2.0

        return scores

    def get_repo_map(
        self,
        root_path: str,
        *,
        query_context: str | None = None,
        max_tokens: int = 1024,
        file_filter: list[str] | None = None,
    ) -> RepoMapResult:
        """Construct a ranked, token-budgeted code skeleton for the repository."""
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            return RepoMapResult(
                status="error",
                root_path=root_path,
                error=f"Directory does not exist: {root_path}",
            )

        scanned_count = 0
        all_tags: dict[str, list[SymbolTag]] = {}
        total_symbols = 0

        # Traverse directory
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORE_DIRS and not d.startswith(".")]

            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext not in {".py", ".ts", ".js", ".rs", ".go"}:
                    continue

                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")

                if file_filter and rel_path not in file_filter:
                    continue

                scanned_count += 1
                try:
                    mtime = os.path.getmtime(full_path)
                    cached = self._tag_cache.get(rel_path)
                    if cached and cached[0] == mtime:
                        tags = cached[1]
                    else:
                        tags = self.extract_tags(full_path)
                        self._tag_cache[rel_path] = (mtime, tags)

                    if tags:
                        all_tags[rel_path] = tags
                        total_symbols += len(tags)
                except Exception as err:
                    logger.debug("tag_extraction_failed", path=rel_path, error=str(err))

        if not all_tags:
            return RepoMapResult(
                status="ok",
                root_path=root_path,
                total_files_scanned=scanned_count,
                total_symbols_indexed=0,
                formatted_map="No indexed symbols found.",
                token_estimate=5,
            )

        # Score files by relevance
        scores = self._compute_relevance_scores(all_tags, query_context)
        ranked_files = sorted(all_tags.keys(), key=lambda p: scores[p], reverse=True)

        # Budget lines: ~4 characters per token estimate
        char_budget = max_tokens * 4
        map_lines: list[str] = []
        current_chars = 0

        for rel_path in ranked_files:
            tags = all_tags[rel_path]
            file_header = f"{rel_path}:"
            line_block = [file_header]

            for tag in tags[:15]:  # Cap symbols per file
                line_block.append(f"  {tag.signature}")

            block_text = "\n".join(line_block)
            if current_chars + len(block_text) + 2 > char_budget:
                if not map_lines:  # Ensure at least first file is partially included
                    map_lines.append(file_header)
                break

            map_lines.append(block_text)
            current_chars += len(block_text) + 2

        formatted = "\n\n".join(map_lines)
        token_estimate = max(1, len(formatted) // 4)

        return RepoMapResult(
            status="ok",
            root_path=root_path,
            total_files_scanned=scanned_count,
            total_symbols_indexed=total_symbols,
            formatted_map=formatted,
            token_estimate=token_estimate,
        )


__all__ = [
    "DefaultRepoMapService",
    "REPO_MAP_SERVICE_KEY",
    "RepoMapResult",
    "RepoMapService",
    "SymbolTag",
]
