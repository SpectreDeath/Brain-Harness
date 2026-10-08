"""Architecture Linter and Coupling Service protocol, models, and ServiceKey."""

from __future__ import annotations

import ast
from collections import defaultdict
import json
import os
import re
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceContext, ServiceKey

logger = structlog.get_logger()


class CircularImportResult(BaseModel):
    """Result of circular import detection."""

    status: str = Field(default="ok", description="Status indicator")
    root_path: str = Field(default="src", description="Scanned source directory")
    total_modules: int = Field(default=0, description="Total internal modules analyzed")
    has_circular_imports: bool = Field(default=False, description="True if any cyclic dependency loops found")
    cycles_count: int = Field(default=0, description="Count of circular import cycles detected")
    cycles: list[list[str]] = Field(default_factory=list, description="Detected circular dependency cycles")
    error: str | None = Field(default=None, description="Error details if analysis failed")


class ModuleCouplingResult(BaseModel):
    """Result of module coupling calculation."""

    status: str = Field(default="ok", description="Status indicator")
    total_modules: int = Field(default=0, description="Total modules analyzed")
    metrics: list[dict[str, Any]] = Field(default_factory=list, description="Afferent (Ca), Efferent (Ce), and Instability (I) metrics")
    error: str | None = Field(default=None, description="Error details if analysis failed")


class BoundaryCheckResult(BaseModel):
    """Result of layer boundary verification."""

    status: str = Field(default="ok", description="Status indicator")
    layer_hierarchy: list[str] = Field(default_factory=list, description="Ordered layer hierarchy enforced")
    clean: bool = Field(default=True, description="True if no inward dependency violations found")
    violations_count: int = Field(default=0, description="Count of layer boundary violations")
    violations: list[dict[str, Any]] = Field(default_factory=list, description="Details of illegal cross-layer imports")
    error: str | None = Field(default=None, description="Error details if check failed")


class FileDiagnostic(BaseModel):
    """Diagnostic issue found during per-file linting."""

    line: int = Field(default=1, description="Line number of diagnostic")
    column: int = Field(default=0, description="Column offset of diagnostic")
    severity: str = Field(default="error", description="Severity: error, warning, info")
    message: str = Field(..., description="Diagnostic error message")
    source: str = Field(default="syntax", description="Linter source: ast, json, yaml, balance")


class FileLintResult(BaseModel):
    """Result of linting a single modified file."""

    status: str = Field(default="ok", description="Status indicator (ok, error, clean)")
    file_path: str = Field(..., description="Path of linted file")
    is_clean: bool = Field(default=True, description="True if no syntax or structural errors found")
    error_count: int = Field(default=0, description="Number of error-level diagnostics found")
    diagnostics: list[FileDiagnostic] = Field(default_factory=list, description="List of diagnostics")
    formatted_summary: str = Field(default="", description="Rendered summary for agent observation injection")
    remediated_code: str | None = Field(default=None, description="Auto-remediated code preview if available")


@runtime_checkable
class ArchLinterService(Protocol):
    """Protocol for architecture linting, circular import detection, and coupling metrics."""

    def detect_circular_imports(self, root_path: str = "src") -> CircularImportResult:
        """Scan a Python directory, build module import graph, and detect circular loops."""
        ...

    def compute_module_coupling(self, root_path: str = "src") -> ModuleCouplingResult:
        """Compute afferent (Ca) and efferent (Ce) coupling and instability metrics."""
        ...

    def verify_clean_boundaries(
        self,
        root_path: str = "src",
        layer_hierarchy: list[str] | None = None,
    ) -> BoundaryCheckResult:
        """Verify that inner architectural layers do not import outer layers."""
        ...

    def lint_file(self, path: str, content: str | None = None) -> FileLintResult:
        """Execute instant syntax and structural lint verification on a file."""
        ...


ARCH_LINTER_KEY: ServiceKey[ArchLinterService] = ServiceKey("service.arch_linter")


def _get_module_name(file_path: Path, root: Path) -> str:
    rel = file_path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _extract_imports(file_path: Path) -> list[str]:
    imported: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    return imported


def _build_dependency_graph(root_path: str = "src") -> tuple[dict[str, set[str]], list[str]]:
    root = Path(root_path).resolve()
    graph: dict[str, set[str]] = defaultdict(set)
    all_modules: list[str] = []

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py"):
                p = Path(dirpath) / f
                mod = _get_module_name(p, root)
                if mod:
                    all_modules.append(mod)
                    raw_imports = _extract_imports(p)
                    for imp in raw_imports:
                        graph[mod].add(imp)

    return graph, all_modules


class DefaultArchLinterService:
    """Default implementation of ArchLinterService with in-memory AST static analysis."""

    def detect_circular_imports(self, root_path: str = "src") -> CircularImportResult:
        """Detect cyclic import loops across Python modules."""
        graph, all_modules = _build_dependency_graph(root_path)

        mod_set = set(all_modules)
        internal_graph: dict[str, set[str]] = defaultdict(set)
        for src, targets in graph.items():
            for t in targets:
                for m in mod_set:
                    if t == m or t.startswith(m + "."):
                        internal_graph[src].add(m)

        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.append(node)

            for neighbor in internal_graph.get(node, set()):
                if neighbor == node:
                    continue
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_slice = rec_stack[rec_stack.index(neighbor) :] + [neighbor]
                    cycles.append(cycle_slice)

            rec_stack.pop()

        for m in all_modules:
            if m not in visited:
                dfs(m)

        return CircularImportResult(
            status="ok",
            root_path=root_path,
            total_modules=len(all_modules),
            has_circular_imports=len(cycles) > 0,
            cycles_count=len(cycles),
            cycles=cycles,
        )

    def compute_module_coupling(self, root_path: str = "src") -> ModuleCouplingResult:
        """Compute afferent (Ca), efferent (Ce), and Instability (I = Ce / (Ca + Ce))."""
        graph, all_modules = _build_dependency_graph(root_path)
        mod_set = set(all_modules)

        efferent: dict[str, set[str]] = defaultdict(set)
        afferent: dict[str, set[str]] = defaultdict(set)

        for src, targets in graph.items():
            for t in targets:
                for m in mod_set:
                    if (t == m or t.startswith(m + ".")) and m != src:
                        efferent[src].add(m)
                        afferent[m].add(src)

        metrics: list[dict[str, Any]] = []
        for m in sorted(all_modules):
            ca = len(afferent[m])
            ce = len(efferent[m])
            instability = round(ce / (ca + ce), 2) if (ca + ce) > 0 else 0.0
            metrics.append({
                "module": m,
                "afferent_coupling_Ca": ca,
                "efferent_coupling_Ce": ce,
                "instability_I": instability,
            })

        return ModuleCouplingResult(
            status="ok",
            total_modules=len(all_modules),
            metrics=metrics,
        )

    def verify_clean_boundaries(
        self,
        root_path: str = "src",
        layer_hierarchy: list[str] | None = None,
    ) -> BoundaryCheckResult:
        """Verify inward dependency rule (inner layers must not import outer layers)."""
        layers = layer_hierarchy or ["kernel", "services", "plugins", "agent", "bridges", "cli", "ui"]
        layer_order = {layer: idx for idx, layer in enumerate(layers)}

        graph, _ = _build_dependency_graph(root_path)
        violations: list[dict[str, Any]] = []

        for src_mod, targets in graph.items():
            src_layer = next((lyr for lyr in layers if f".{lyr}" in f".{src_mod}" or src_mod.startswith(lyr)), None)
            if not src_layer:
                continue
            src_idx = layer_order[src_layer]

            for target in targets:
                tgt_layer = next((lyr for lyr in layers if f".{lyr}" in f".{target}" or target.startswith(lyr)), None)
                if not tgt_layer or tgt_layer == src_layer:
                    continue
                tgt_idx = layer_order[tgt_layer]

                # Inward dependency rule violation (lower index importing higher index)
                if src_idx < tgt_idx:
                    violations.append({
                        "source_module": src_mod,
                        "source_layer": src_layer,
                        "target_module": target,
                        "target_layer": tgt_layer,
                        "detail": f"Inner layer '{src_layer}' (level {src_idx}) illegally imports outer layer '{tgt_layer}' (level {tgt_idx}).",
                    })

        return BoundaryCheckResult(
            status="ok",
            layer_hierarchy=layers,
            clean=len(violations) == 0,
            violations_count=len(violations),
            violations=violations,
        )

    def lint_file(self, path: str, content: str | None = None) -> FileLintResult:
        """Execute fast syntax and structural validation on edited files."""
        p = Path(path)
        ext = p.suffix.lower()

        if content is None:
            if not p.exists():
                return FileLintResult(
                    status="error",
                    file_path=path,
                    is_clean=False,
                    error_count=1,
                    diagnostics=[FileDiagnostic(line=1, severity="error", message=f"File not found: {path}", source="filesystem")],
                    formatted_summary=f"LINT ERROR [{path}]: File not found",
                )
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as err:
                return FileLintResult(
                    status="error",
                    file_path=path,
                    is_clean=False,
                    error_count=1,
                    diagnostics=[FileDiagnostic(line=1, severity="error", message=str(err), source="filesystem")],
                    formatted_summary=f"LINT ERROR [{path}]: {err}",
                )

        diagnostics: list[FileDiagnostic] = []

        if ext == ".py":
            try:
                ast.parse(content, filename=path)
            except SyntaxError as err:
                diagnostics.append(
                    FileDiagnostic(
                        line=err.lineno or 1,
                        column=err.offset or 0,
                        severity="error",
                        message=f"SyntaxError: {err.msg}",
                        source="python_ast",
                    )
                )

        elif ext == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as err:
                diagnostics.append(
                    FileDiagnostic(
                        line=err.lineno,
                        column=err.colno,
                        severity="error",
                        message=f"JSONDecodeError: {err.msg}",
                        source="json",
                    )
                )

        # Check bracket balancing for all languages
        stack: list[tuple[str, int]] = []
        pairs = {")": "(", "}": "{", "]": "["}
        opens = set(pairs.values())

        for idx, line in enumerate(content.splitlines(), start=1):
            for char in line:
                if char in opens:
                    stack.append((char, idx))
                elif char in pairs:
                    if not stack or stack[-1][0] != pairs[char]:
                        diagnostics.append(
                            FileDiagnostic(
                                line=idx,
                                severity="error",
                                message=f"Unmatched closing delimiter '{char}'",
                                source="balance",
                            )
                        )
                    else:
                        stack.pop()

        if stack and len(diagnostics) == 0:
            unmatched_char, un_line = stack[-1]
            diagnostics.append(
                FileDiagnostic(
                    line=un_line,
                    severity="error",
                    message=f"Unclosed opening delimiter '{unmatched_char}'",
                    source="balance",
                )
            )

        is_clean = len(diagnostics) == 0
        summary = ""
        if not is_clean:
            lines_diag = [f"  Line {d.line}:{d.column} - {d.message}" for d in diagnostics]
            summary = f"LINT DIAGNOSTICS ({len(diagnostics)} errors in {path}):\n" + "\n".join(lines_diag)

        return FileLintResult(
            status="ok" if is_clean else "error",
            file_path=path,
            is_clean=is_clean,
            error_count=len(diagnostics),
            diagnostics=diagnostics,
            formatted_summary=summary,
        )


def resolve_arch_linter(ctx: ServiceContext | None = None) -> ArchLinterService:
    """Resolve ArchLinterService from ServiceContext or fall back to DefaultArchLinterService."""
    if ctx is not None:
        svc = ctx.optional(ARCH_LINTER_KEY)
        if svc is not None and isinstance(svc, ArchLinterService):
            return svc
    return DefaultArchLinterService()


__all__ = [
    "ARCH_LINTER_KEY",
    "ArchLinterService",
    "BoundaryCheckResult",
    "CircularImportResult",
    "DefaultArchLinterService",
    "FileDiagnostic",
    "FileLintResult",
    "ModuleCouplingResult",
    "resolve_arch_linter",
]
