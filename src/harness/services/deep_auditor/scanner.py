"""Bounded filesystem scanner and nested project root resolver (Rule 52)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_PRUNE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".harness",
        "external",
        "test_ingested_plugins",
        ".gemini",
        "dist",
        "build",
        "target",
    }
)
_MANIFEST_NAMES: tuple[str, ...] = ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml")
_MAX_SCAN_DEPTH = 4


@dataclass(slots=True)
class _ScanStats:
    total_files: int = 0
    python_files: int = 0
    plugin_manifests: int = 0
    skill_specs: int = 0
    test_files: int = 0
    async_hits: int = 0
    workflow_files: int = 0
    has_changelog: bool = False
    blast_modules: list[str] | None = None

    def __post_init__(self) -> None:
        if self.blast_modules is None:
            self.blast_modules = []


def resolve_nested_project_root(root: Path) -> tuple[Path, str, int]:
    """Probe nested directories (max depth 3) for canonical project manifests."""
    current = root.resolve()
    best_dir = current
    best_manifest = "none"
    best_depth = 0
    for depth in range(4):
        for name in _MANIFEST_NAMES:
            if (current / name).is_file():
                best_dir = current
                best_manifest = name
                best_depth = depth
                break
        if best_manifest != "none":
            break
        subdirs = [d for d in sorted(current.iterdir()) if d.is_dir() and d.name not in _PRUNE_DIRS]
        if len(subdirs) != 1:
            break
        current = subdirs[0]
    return best_dir, best_manifest, best_depth


def scan_repository_tree(root: Path) -> _ScanStats:
    """Execute bounded os.walk pruning noise directories and collecting structural counts."""
    stats = _ScanStats()
    root_depth = len(root.parts)
    for cur, dirs, files in os.walk(root):
        cur_path = Path(cur)
        depth = len(cur_path.parts) - root_depth
        dirs[:] = [d for d in sorted(dirs) if d not in _PRUNE_DIRS and depth < _MAX_SCAN_DEPTH]
        for fname in sorted(files):
            stats.total_files += 1
            fpath = cur_path / fname
            rel = str(fpath.relative_to(root)).replace("\\", "/")
            if fname == "plugin.json":
                stats.plugin_manifests += 1
            elif fname == "SKILL.md":
                stats.skill_specs += 1
            elif fname.upper().startswith("CHANGELOG"):
                stats.has_changelog = True
            if ".github/workflows" in rel and fname.endswith((".yml", ".yaml")):
                stats.workflow_files += 1
            if fname.endswith(".py"):
                stats.python_files += 1
                if fname.startswith("test_") or "/tests/" in f"/{rel}":
                    stats.test_files += 1
                elif depth <= 3 and len(stats.blast_modules or []) < 12:
                    (stats.blast_modules or []).append(rel)
                if stats.python_files <= 60:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")[:8192]
                    if "async def " in text:
                        stats.async_hits += 1
    return stats


__all__ = ["_ScanStats", "resolve_nested_project_root", "scan_repository_tree"]
