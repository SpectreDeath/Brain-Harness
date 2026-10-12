"""AST symbol visitor, name extraction, and BFS reachability resolution."""

from __future__ import annotations

import ast
from pathlib import Path

from plugins.memory_and_epistemics.context_compiler.compiler_core.constants import (
    _BUILTIN_NAMES,
    KNOWN_EVENT_DECORATORS,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.models import (
    FileSymbols,
    ReachabilityResult,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.module_index import ModuleIndex


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return None


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols = FileSymbols()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.symbols.imported_modules.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.symbols.imported_modules.add(node.module)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute):
            self.symbols.called_names.add(func.attr)
        elif isinstance(func, ast.Name):
            self.symbols.called_names.add(func.id)
            if func.id == "getattr":
                self.symbols.uses_dynamic_dispatch = True
        self.generic_visit(node)

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.symbols.defined_names.add(node.name)
        for deco in node.decorator_list:
            name = _decorator_name(deco)
            if name:
                self.symbols.uses_decorators.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.defined_names.add(node.name)
        self.generic_visit(node)


def extract_symbols(source: str) -> FileSymbols:
    """Parse Python source and extract imported modules, called symbols, and definitions."""
    tree = ast.parse(source)
    visitor = _SymbolVisitor()
    visitor.visit(tree)
    return visitor.symbols


class SymbolResolver:
    """Builds an approximate reachability graph outward from a target file."""

    def __init__(self, repo_root: str | Path, max_hops: int = 2) -> None:
        self.root = Path(repo_root).resolve()
        self.max_hops = max_hops
        self.index = ModuleIndex.build(self.root)
        self._symbol_table: dict[str, list[Path]] | None = None

    def _global_symbol_table(self) -> dict[str, list[Path]]:
        if self._symbol_table is not None:
            return self._symbol_table
        table: dict[str, list[Path]] = {}
        for path in self.index.path_to_module:
            try:
                source = path.read_text(encoding="utf-8")
                symbols = extract_symbols(source)
            except (SyntaxError, UnicodeDecodeError):
                continue
            for name in symbols.defined_names:
                table.setdefault(name, []).append(path)
        self._symbol_table = table
        return table

    def resolve(self, target_file: str | Path) -> ReachabilityResult:
        """Resolve outward dependency graph via BFS up to max_hops."""
        target_path = Path(target_file).resolve()
        result = ReachabilityResult()
        visited = {target_path}
        symbol_table = self._global_symbol_table()

        hop = 0
        current_layer = [target_path]
        while current_layer and hop < self.max_hops:
            hop += 1
            next_layer: list[Path] = []
            for file_path in current_layer:
                try:
                    source = file_path.read_text(encoding="utf-8")
                    symbols = extract_symbols(source)
                except (SyntaxError, UnicodeDecodeError):
                    continue

                if symbols.uses_dynamic_dispatch:
                    result.dynamic_dispatch_files.add(file_path)

                event_decorators = symbols.uses_decorators & KNOWN_EVENT_DECORATORS
                if event_decorators:
                    result.decorator_hint_files[file_path] = event_decorators

                # (a) explicit imports
                for module_name in symbols.imported_modules:
                    resolved = self.index.resolve_import(module_name)
                    if resolved and resolved not in visited:
                        visited.add(resolved)
                        result.reachable[resolved] = hop
                        next_layer.append(resolved)

                # (b) name-only call resolution
                for called_name in symbols.called_names:
                    if called_name in _BUILTIN_NAMES or called_name.startswith("__"):
                        continue
                    candidates = symbol_table.get(called_name)
                    if not candidates:
                        result.unresolved_calls.add(called_name)
                        continue
                    if len(candidates) > 1:
                        result.name_collisions[called_name] = candidates
                    for candidate in candidates:
                        if candidate not in visited:
                            visited.add(candidate)
                            result.reachable[candidate] = hop
                            next_layer.append(candidate)

            current_layer = next_layer

        result.reachable.pop(target_path, None)
        return result
