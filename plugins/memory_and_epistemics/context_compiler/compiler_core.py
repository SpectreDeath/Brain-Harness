"""Core AST skeletonizing, symbol reachability analysis, and 3-tier context compilation engine."""

from __future__ import annotations

import ast
import builtins
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_BUILTIN_NAMES = set(dir(builtins))
KNOWN_EVENT_DECORATORS = {"receiver", "signal", "event", "on", "hook", "register", "route"}
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count with 4 chars/token heuristic."""
    return max(1, len(text) // CHARS_PER_TOKEN)


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
        import json

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
            if trimmed.startswith("#") or trimmed.startswith("```") or trimmed.startswith("- ") or trimmed.startswith("* "):
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


@dataclass
class ModuleIndex:
    """Maps every .py file in a repository to its dotted module path, and back."""

    root: Path
    path_to_module: dict[Path, str] = field(default_factory=dict)
    module_to_path: dict[str, Path] = field(default_factory=dict)

    @classmethod
    def build(cls, root: Path) -> ModuleIndex:
        index = cls(root=root.resolve())
        for py_file in root.rglob("*.py"):
            if any(part in {".git", "venv", ".venv", "__pycache__", "node_modules", ".tox", ".mypy_cache"} for part in py_file.parts):
                continue
            try:
                rel = py_file.relative_to(root)
            except ValueError:
                continue
            parts = list(rel.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            module = ".".join(parts) if parts else rel.stem
            index.path_to_module[py_file.resolve()] = module
            if module:
                index.module_to_path[module] = py_file.resolve()
        return index

    def resolve_import(self, module_name: str) -> Path | None:
        """Best-effort resolution of a dotted import name to a file in the repo."""
        if module_name in self.module_to_path:
            return self.module_to_path[module_name]
        parts = module_name.split(".")
        while len(parts) > 1:
            parts.pop()
            candidate = ".".join(parts)
            if candidate in self.module_to_path:
                return self.module_to_path[candidate]
        return None


@dataclass
class FileSymbols:
    imported_modules: set[str] = field(default_factory=set)
    called_names: set[str] = field(default_factory=set)
    defined_names: set[str] = field(default_factory=set)
    uses_dynamic_dispatch: bool = False
    uses_decorators: set[str] = field(default_factory=set)


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
    tree = ast.parse(source)
    visitor = _SymbolVisitor()
    visitor.visit(tree)
    return visitor.symbols


@dataclass
class ReachabilityResult:
    reachable: dict[Path, int] = field(default_factory=dict)  # path -> hop distance
    unresolved_calls: set[str] = field(default_factory=set)
    dynamic_dispatch_files: set[Path] = field(default_factory=set)
    decorator_hint_files: dict[Path, set[str]] = field(default_factory=dict)
    name_collisions: dict[str, list[Path]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reachable_files": {str(k): v for k, v in self.reachable.items()},
            "unresolved_calls": sorted(self.unresolved_calls),
            "dynamic_dispatch_files": [str(p) for p in self.dynamic_dispatch_files],
            "decorator_hint_files": {str(k): sorted(v) for k, v in self.decorator_hint_files.items()},
            "name_collisions": {k: [str(p) for p in v] for k, v in self.name_collisions.items()},
        }


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


@dataclass
class TierEntry:
    path: Path
    tier: int
    content: str
    tokens: int
    hop_distance: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "tier": self.tier,
            "tokens": self.tokens,
            "hop_distance": self.hop_distance,
        }


@dataclass
class CompiledContext:
    target_file: Path
    entries: list[TierEntry] = field(default_factory=list)
    excluded_count: int = 0
    total_repo_files: int = 0
    naive_dump_tokens: int = 0
    compiled_tokens: int = 0
    build_seconds: float = 0.0
    diagnostics: ReachabilityResult | None = None

    def to_prompt_string(self) -> str:
        parts = []
        for entry in self.entries:
            label = "FULL SOURCE" if entry.tier == 1 else "SKELETON"
            parts.append(f"# ---- [{label}] {entry.path} ----\n{entry.content}")
        return "\n\n".join(parts)

    def reduction_pct(self) -> float:
        if self.naive_dump_tokens == 0:
            return 0.0
        return 100.0 * (1.0 - (self.compiled_tokens / self.naive_dump_tokens))

    def summary(self) -> str:
        tier2 = sum(1 for e in self.entries if e.tier == 2)
        lines = [
            f"Target file: {self.target_file}",
            f"Repo files scanned: {self.total_repo_files}",
            "Tier 1 (full source): 1 file",
            f"Tier 2 (skeletonized): {tier2} files",
            f"Tier 3 (excluded): {self.excluded_count} files",
            f"Naive full-dump estimate: {self.naive_dump_tokens} tokens",
            f"Compiled context: {self.compiled_tokens} tokens",
            f"Reduction: {self.reduction_pct():.1f}%",
            f"Build time: {self.build_seconds * 1000:.2f} ms",
        ]
        if self.diagnostics:
            if self.diagnostics.dynamic_dispatch_files:
                lines.append(
                    f"Warning: {len(self.diagnostics.dynamic_dispatch_files)} file(s) use "
                    f"getattr()-based dynamic dispatch — targets may be missing from tier 2."
                )
            if self.diagnostics.decorator_hint_files:
                lines.append(
                    f"Warning: {len(self.diagnostics.decorator_hint_files)} file(s) use "
                    f"event-style decorators — handlers may be missing from tier 2."
                )
            if self.diagnostics.name_collisions:
                lines.append(
                    f"Note: {len(self.diagnostics.name_collisions)} call name(s) resolved to "
                    f"more than one file — tier 2 may include false positives."
                )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": str(self.target_file),
            "total_repo_files": self.total_repo_files,
            "tier1_files": 1,
            "tier2_files": sum(1 for e in self.entries if e.tier == 2),
            "tier3_excluded_files": self.excluded_count,
            "naive_dump_tokens": self.naive_dump_tokens,
            "compiled_tokens": self.compiled_tokens,
            "reduction_pct": round(self.reduction_pct(), 2),
            "build_ms": round(self.build_seconds * 1000, 2),
            "entries": [e.to_dict() for e in self.entries],
            "diagnostics": self.diagnostics.to_dict() if self.diagnostics else None,
            "summary": self.summary(),
        }


class ContextCompiler:
    """Orchestrates 3-tier AST context compilation for agent workflows."""

    def __init__(self, repo_root: str | Path, max_hops: int = 2) -> None:
        self.root = Path(repo_root).resolve()
        self.max_hops = max_hops
        self.resolver = SymbolResolver(self.root, max_hops=max_hops)

    def compile(self, target_file: str | Path) -> CompiledContext:
        start = time.perf_counter()
        target_path = Path(target_file).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {target_path}")

        target_source = target_path.read_text(encoding="utf-8")
        reachability = self.resolver.resolve(target_path)

        entries = [
            TierEntry(
                path=target_path,
                tier=1,
                content=target_source,
                tokens=estimate_tokens(target_source),
                hop_distance=0,
            )
        ]

        for dep_path, hop in sorted(reachability.reachable.items(), key=lambda kv: kv[1]):
            try:
                source = dep_path.read_text(encoding="utf-8", errors="replace")
                skeleton, _ = SkeletonizerRegistry.skeletonize(dep_path, source)
            except Exception:
                continue
            entries.append(
                TierEntry(
                    path=dep_path,
                    tier=2,
                    content=skeleton,
                    tokens=estimate_tokens(skeleton),
                    hop_distance=hop,
                )
            )

        all_py_files = list(self.resolver.index.path_to_module.keys())
        included_paths = {e.path for e in entries}
        excluded_count = max(0, len(all_py_files) - len(included_paths))

        naive_dump_tokens = 0
        for path in all_py_files:
            try:
                naive_dump_tokens += estimate_tokens(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue

        compiled_tokens = sum(e.tokens for e in entries)

        return CompiledContext(
            target_file=target_path,
            entries=entries,
            excluded_count=excluded_count,
            total_repo_files=len(all_py_files),
            naive_dump_tokens=naive_dump_tokens,
            compiled_tokens=compiled_tokens,
            build_seconds=time.perf_counter() - start,
            diagnostics=reachability,
        )
