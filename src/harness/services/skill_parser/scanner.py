"""Bounded filesystem directory scanner for skill discovery per Rule 52."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from harness.services.skill_graph.models import SkillCardDefinition


def scan_root(
    root_path: Path,
    max_depth: int = 4,
    parse_directory_fn: Callable[[Path], SkillCardDefinition | None] | None = None,
) -> dict[str, SkillCardDefinition]:
    """Scan a root directory for all valid skill folders, enforcing Rule 52 bounded traversal."""
    skills: dict[str, SkillCardDefinition] = {}
    if not root_path.exists():
        return skills

    ignored_parts = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "venvs",
        "site-packages",
        "__pycache__",
        "target",
        "dist",
        ".gemini",
    }

    resolved_root = root_path.resolve()
    for root, dirs, files in os.walk(resolved_root):
        dirs[:] = [
            d
            for d in dirs
            if d.lower() not in ignored_parts and not d.startswith(".")
        ]
        current_path = Path(root)
        try:
            rel = current_path.relative_to(resolved_root)
            depth = len(rel.parts)
        except ValueError:
            depth = 0

        if depth > max_depth:
            dirs.clear()
            continue

        if "SKILL.md" in files or "CARD.md" in files:
            if parse_directory_fn:
                try:
                    node = parse_directory_fn(current_path)
                    if node:
                        skills[node.name] = node
                except Exception:
                    pass

    return skills
