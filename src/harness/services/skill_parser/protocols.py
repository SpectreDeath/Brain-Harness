"""Service protocol and typed ServiceKey for SkillCardParser."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.skill_graph.models import SkillCardDefinition


@runtime_checkable
class SkillCardParserService(Protocol):
    """Protocol for parsing agent skill folders into canonical SkillCardDefinitions."""

    def parse_directory(self, dir_path: Path) -> SkillCardDefinition | None:
        """Parse a skill directory containing SKILL.md and/or CARD.md."""
        ...

    def scan_root(self, root_path: Path, max_depth: int = 4) -> dict[str, SkillCardDefinition]:
        """Scan a root directory for all valid skill folders."""
        ...


SKILL_PARSER_SERVICE_KEY: ServiceKey[SkillCardParserService] = ServiceKey("skill_parser.service")
