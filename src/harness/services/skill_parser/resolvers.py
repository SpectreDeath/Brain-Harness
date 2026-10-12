"""Single-seam resolver for SkillCardParser per Rule 58."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from harness.services.skill_parser.parser import SkillCardParser
from harness.services.skill_parser.protocols import (
    SKILL_PARSER_SERVICE_KEY,
    SkillCardParserService,
)


class DefaultSkillCardParserService:
    """Default service adapter delegating to SkillCardParser."""

    def parse_directory(self, dir_path):
        return SkillCardParser.parse_directory(dir_path)

    def scan_root(self, root_path, max_depth: int = 4):
        return SkillCardParser.scan_root(root_path, max_depth=max_depth)


_DEFAULT_SERVICE = DefaultSkillCardParserService()


def resolve_skill_card_parser(
    context: ServiceContext | None = None,
) -> SkillCardParserService:
    """Resolve SkillCardParserService from IoC container if available, else default."""
    if context and context.has(SKILL_PARSER_SERVICE_KEY):
        return context.require(SKILL_PARSER_SERVICE_KEY)
    return _DEFAULT_SERVICE
