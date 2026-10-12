"""Repository module indexing and import path resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ModuleIndex:
    """Maps every .py file in a repository to its dotted module path, and back."""

    root: Path
    path_to_module: dict[Path, str] = field(default_factory=dict)
    module_to_path: dict[str, Path] = field(default_factory=dict)

    @classmethod
    def build(cls, root: Path) -> ModuleIndex:
        """Scan repository directory and construct bidirectional module map."""
        index = cls(root=root.resolve())
        # Prune noise directories per Rule 52
        noise_dirs = {".git", "venv", ".venv", "__pycache__", "node_modules", ".tox", ".mypy_cache", "dist", "build"}
        for py_file in root.rglob("*.py"):
            if any(part in noise_dirs for part in py_file.parts):
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
