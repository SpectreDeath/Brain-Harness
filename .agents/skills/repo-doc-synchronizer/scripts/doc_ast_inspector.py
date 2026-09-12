"""
Fast AST-based code inspector extracting public symbols, classes, functions, and docstrings.
Enforces Rule 12: Slotted & Frozen Dataclass Architecture.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class FunctionSymbol:
    """Represents an inspected function or method."""

    name: str
    args: tuple[str, ...]
    return_annotation: str | None
    docstring: str | None
    is_async: bool
    is_method: bool
    lineno: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "args": list(self.args),
            "return_annotation": self.return_annotation,
            "docstring": self.docstring,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "lineno": self.lineno,
        }


@dataclass(slots=True, frozen=True)
class ClassSymbol:
    """Represents an inspected class and its methods."""

    name: str
    docstring: str | None
    bases: tuple[str, ...]
    methods: tuple[FunctionSymbol, ...]
    lineno: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "docstring": self.docstring,
            "bases": list(self.bases),
            "methods": [m.to_dict() for m in self.methods],
            "lineno": self.lineno,
        }


@dataclass(slots=True, frozen=True)
class ModuleInspection:
    """Complete AST profile of a Python module file."""

    file_path: str
    module_name: str
    docstring: str | None
    classes: tuple[ClassSymbol, ...]
    functions: tuple[FunctionSymbol, ...]
    exported_names: tuple[str, ...]
    has_module_docstring: bool
    total_public_symbols: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "module_name": self.module_name,
            "docstring": self.docstring,
            "has_module_docstring": self.has_module_docstring,
            "total_public_symbols": self.total_public_symbols,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "exported_names": list(self.exported_names),
        }


def _get_annotation_str(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def inspect_module_ast(file_path: Path) -> ModuleInspection | None:
    """Extracts classes, functions, docstrings, and exports from a Python file."""
    p = Path(file_path)
    if not p.exists() or p.suffix != ".py":
        return None

    try:
        source = p.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(p))
    except Exception:
        return None

    module_doc = ast.get_docstring(tree)
    classes: list[ClassSymbol] = []
    functions: list[FunctionSymbol] = []
    exported_names: list[str] = []

    # Look for __all__
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__all__"
                    and isinstance(node.value, (ast.List, ast.Tuple))
                ):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            exported_names.append(elt.value)

        # Inspect classes
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue  # Skip internal private classes
            class_doc = ast.get_docstring(node)
            bases = tuple(_get_annotation_str(b) or "object" for b in node.bases)
            methods: list[FunctionSymbol] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_") and item.name not in (
                        "__init__",
                        "__post_init__",
                    ):
                        continue
                    args = tuple(arg.arg for arg in item.args.args if arg.arg != "self")
                    ret_ann = _get_annotation_str(item.returns)
                    method_doc = ast.get_docstring(item)
                    methods.append(
                        FunctionSymbol(
                            name=item.name,
                            args=args,
                            return_annotation=ret_ann,
                            docstring=method_doc,
                            is_async=isinstance(item, ast.AsyncFunctionDef),
                            is_method=True,
                            lineno=item.lineno,
                        )
                    )
            classes.append(
                ClassSymbol(
                    name=node.name,
                    docstring=class_doc,
                    bases=bases,
                    methods=tuple(methods),
                    lineno=node.lineno,
                )
            )

        # Inspect top-level functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue  # Skip internal private functions
            args = tuple(arg.arg for arg in node.args.args)
            ret_ann = _get_annotation_str(node.returns)
            fn_doc = ast.get_docstring(node)
            functions.append(
                FunctionSymbol(
                    name=node.name,
                    args=args,
                    return_annotation=ret_ann,
                    docstring=fn_doc,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    is_method=False,
                    lineno=node.lineno,
                )
            )

    public_symbol_count = len(classes) + len(functions)
    rel_path = str(p).replace("\\", "/")

    return ModuleInspection(
        file_path=rel_path,
        module_name=p.stem,
        docstring=module_doc,
        classes=tuple(classes),
        functions=tuple(functions),
        exported_names=tuple(exported_names),
        has_module_docstring=module_doc is not None and bool(module_doc.strip()),
        total_public_symbols=public_symbol_count,
    )
