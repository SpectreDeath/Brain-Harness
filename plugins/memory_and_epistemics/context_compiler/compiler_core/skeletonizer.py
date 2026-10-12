"""Polyglot AST skeletonizer for code, JSON, Markdown, and text."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


class CodeSkeletonizer(ast.NodeTransformer):
    """Strips function and method bodies, leaving only signatures and docstrings."""

    def __init__(self) -> None:
        super().__init__()
        self.functions_stripped = 0

    @staticmethod
    def _docstring_node(node: ast.AST) -> ast.Expr | None:
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[0]
        return None

    def _strip_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.FunctionDef | ast.AsyncFunctionDef:
        self.functions_stripped += 1
        doc = self._docstring_node(node)
        placeholder = ast.Expr(
            value=ast.Constant(value=...),
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        node.body = [doc, placeholder] if doc is not None else [placeholder]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        return self._strip_body(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        self.generic_visit(node)
        return self._strip_body(node)

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Keep only top-level imports, classes, and function defs."""
        self.generic_visit(node)
        kept_body = []
        for item in node.body:
            if isinstance(item, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                kept_body.append(item)
            elif (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            ):
                kept_body.append(item)  # module docstring
        node.body = kept_body
        return node


def skeletonize_source(source: str) -> tuple[str, int]:
    """Reduce Python source code to its structural interface skeleton.

    Returns:
        (skeletonized_source, functions_stripped_count)
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Cannot skeletonize unparseable source: {e}") from e

    skeletonizer = CodeSkeletonizer()
    skeleton_tree = skeletonizer.visit(tree)
    ast.fix_missing_locations(skeleton_tree)
    return ast.unparse(skeleton_tree), skeletonizer.functions_stripped


class SkeletonizerRegistry:
    """Polyglot structural skeletonizer registry handling Python, JSON, Markdown, and text."""

    @staticmethod
    def skeletonize_json(content: str, max_items: int = 5) -> tuple[str, int]:
        """Summarize JSON content into its structural schema outline."""
        try:
            data = json.loads(content)
        except Exception:
            return content[:300] + "\n... [truncated]", 1

        def _summarize(val: Any, depth: int = 0) -> Any:
            if depth > 3:
                return "..."
            if isinstance(val, dict):
                return {k: _summarize(v, depth + 1) for i, (k, v) in enumerate(val.items()) if i < max_items}
            if isinstance(val, list):
                if not val:
                    return []
                return [_summarize(val[0], depth + 1), f"... ({len(val)} items)"]
            return type(val).__name__

        outline = _summarize(data)
        return json.dumps(outline, indent=2), 1

    @staticmethod
    def skeletonize_markdown(content: str) -> tuple[str, int]:
        """Extract markdown structural outline (headings, code blocks, lists)."""
        lines = content.splitlines()
        outline_lines = []
        stripped = 0
        for line in lines:
            trimmed = line.strip()
            if (
                trimmed.startswith("#")
                or trimmed.startswith("```")
                or trimmed.startswith("- ")
                or trimmed.startswith("* ")
            ):
                outline_lines.append(line)
            else:
                stripped += 1
        res = "\n".join(outline_lines) if outline_lines else content[:300]
        return res, stripped

    @classmethod
    def skeletonize(cls, path: Path | str, content: str | None = None) -> tuple[str, int]:
        """Skeletonize a file based on its file extension."""
        p = Path(path)
        text = content if content is not None else p.read_text(encoding="utf-8", errors="replace")
        suffix = p.suffix.lower()

        if suffix in {".py", ".pyi"}:
            try:
                return skeletonize_source(text)
            except Exception:
                return text[:500] + "\n... [parse fallback]", 1
        elif suffix == ".json":
            return cls.skeletonize_json(text)
        elif suffix in {".md", ".markdown"}:
            return cls.skeletonize_markdown(text)
        else:
            # General text fallback
            lines = text.splitlines()
            if len(lines) > 20:
                head = "\n".join(lines[:10])
                tail = "\n".join(lines[-10:])
                return f"{head}\n\n# ... [{len(lines) - 20} lines omitted] ...\n\n{tail}", len(lines) - 20
            return text, 0
