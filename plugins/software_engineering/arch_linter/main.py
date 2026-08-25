"""Architecture Linter plugin — circular imports, module coupling, and layer boundary enforcement."""

from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.arch_linter import (
    ARCH_LINTER_KEY,
    ArchLinterService,
    BoundaryCheckResult,
    CircularImportResult,
    ModuleCouplingResult,
)

logger = structlog.get_logger(__name__)


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
                        # Match internal imports
                        graph[mod].add(imp)

    return graph, all_modules


def detect_circular_imports(root_path: str = "src") -> dict[str, Any]:
    """Detect cyclic import loops across Python modules."""
    graph, all_modules = _build_dependency_graph(root_path)

    # Filter graph to only internal modules
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

    return {
        "status": "ok",
        "root_path": root_path,
        "total_modules": len(all_modules),
        "has_circular_imports": len(cycles) > 0,
        "cycles_count": len(cycles),
        "cycles": cycles,
    }


def compute_module_coupling(root_path: str = "src") -> dict[str, Any]:
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

    return {
        "status": "ok",
        "total_modules": len(all_modules),
        "metrics": metrics,
    }


def verify_clean_boundaries(
    root_path: str = "src",
    layer_hierarchy: list[str] | None = None,
) -> dict[str, Any]:
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

    return {
        "status": "ok",
        "layer_hierarchy": layers,
        "clean": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations,
    }


class ArchLinterPlugin(HarnessPlugin, ArchLinterService):
    """Harness Plugin providing codebase coupling, cohesion, and boundary linting."""

    name = "plugin.arch_linter"
    version = "1.0.0"
    description = "Codebase coupling/cohesion analyzer, circular import detector, and clean architecture boundary verifier"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ARCH_LINTER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(ARCH_LINTER_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # ArchLinterService Protocol Implementation
    # -------------------------------------------------------------------------

    def detect_circular_imports(self, root_path: str = "src") -> CircularImportResult:
        res = detect_circular_imports(root_path=root_path)
        return CircularImportResult(
            status=res["status"],
            root_path=res.get("root_path", root_path),
            total_modules=res.get("total_modules", 0),
            has_circular_imports=res.get("has_circular_imports", False),
            cycles_count=res.get("cycles_count", 0),
            cycles=res.get("cycles", []),
            error=res.get("error"),
        )

    def compute_module_coupling(self, root_path: str = "src") -> ModuleCouplingResult:
        res = compute_module_coupling(root_path=root_path)
        return ModuleCouplingResult(
            status=res["status"],
            total_modules=res.get("total_modules", 0),
            metrics=res.get("metrics", []),
            error=res.get("error"),
        )

    def verify_clean_boundaries(
        self,
        root_path: str = "src",
        layer_hierarchy: list[str] | None = None,
    ) -> BoundaryCheckResult:
        res = verify_clean_boundaries(root_path=root_path, layer_hierarchy=layer_hierarchy)
        return BoundaryCheckResult(
            status=res["status"],
            layer_hierarchy=res.get("layer_hierarchy", layer_hierarchy or []),
            clean=res.get("clean", True),
            violations_count=res.get("violations_count", 0),
            violations=res.get("violations", []),
            error=res.get("error"),
        )
