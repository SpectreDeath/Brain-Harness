"""Domain configuration and result models for agent skill creation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from harness.creator.validator import ValidationReport


@dataclass(slots=True)
class SkillOptions:
    """Configuration options for scaffolding a high-precision agent skill."""

    name: str
    description: str = ""
    category: str = "engineering / meta-skills"
    version: str = "1.0.0"
    triggers: list[str] = field(default_factory=list)
    target: str = ""
    stages: list[dict[str, str]] = field(default_factory=list)
    anti_patterns: list[dict[str, str]] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    vocabulary: dict[str, str] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)
    include_card: bool = True
    include_readme: bool = True
    auto_validate: bool = False


@dataclass(slots=True)
class SkillResult(os.PathLike[str]):
    """Structured result returned from skill scaffolding."""

    path: Path
    skill_file: Path
    card_file: Path | None
    generated_files: list[Path] = field(default_factory=list)
    validation_report: ValidationReport | None = None

    @property
    def files_count(self) -> int:
        return len(self.generated_files)

    def __fspath__(self) -> str:
        return str(self.path)

    def __str__(self) -> str:
        return str(self.path)

    def __truediv__(self, other: str | Path) -> Path:
        return self.path / other

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "skill_file": str(self.skill_file),
            "card_file": str(self.card_file) if self.card_file else None,
            "generated_files": [str(f) for f in self.generated_files],
            "files_count": self.files_count,
            "validation_report": self.validation_report.to_dict() if self.validation_report else None,
        }
