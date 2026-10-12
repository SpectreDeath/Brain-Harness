"""SkillCardParser coordinator analyzing SKILL.md and CARD.md files."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from harness.services.skill_graph.models import (
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillInvariantDefinition,
    SkillStageDefinition,
)
from harness.services.skill_parser.card_box import extract_ascii_card
from harness.services.skill_parser.extractors import (
    extract_anti_patterns,
    extract_invariants,
    extract_references,
    extract_stages_from_card_table,
    extract_stages_from_skill_md,
)
from harness.services.skill_parser.frontmatter import extract_frontmatter
from harness.services.skill_parser.scanner import scan_root as scan_root_fn


class SkillCardParser:
    """Authoritative parser for CARD.md and SKILL.md agent skill files."""

    @classmethod
    def parse_directory(cls, dir_path: Path) -> SkillCardDefinition | None:
        """Parse a skill directory containing SKILL.md and/or CARD.md into a canonical SkillCardDefinition."""
        skill_file = dir_path / "SKILL.md"
        card_file = dir_path / "CARD.md"

        if not skill_file.exists() and not card_file.exists():
            return None

        name = dir_path.name
        description = ""
        category = "general"
        version = "1.0.0"
        invocation = f"/{name}"
        triggers: list[str] = []
        target = ""
        stages: list[SkillStageDefinition] = []
        anti_patterns: list[SkillAntiPatternDefinition] = []
        invariants: list[SkillInvariantDefinition] = []
        references: list[str] = []

        if skill_file.exists():
            skill_text = skill_file.read_text(encoding="utf-8", errors="ignore")
            frontmatter, body = extract_frontmatter(skill_text)

            if "name" in frontmatter:
                name = str(frontmatter["name"]).strip()
            if "description" in frontmatter:
                description = str(frontmatter["description"]).strip()
            if "dependencies" in frontmatter:
                deps = frontmatter["dependencies"]
                if isinstance(deps, list):
                    for d in deps:
                        clean_d = str(d).strip().lower().replace("_", "-").lstrip("/")
                        if clean_d and clean_d != name and clean_d not in references:
                            references.append(clean_d)
                elif isinstance(deps, str):
                    for d in deps.split(","):
                        clean_d = d.strip().lower().replace("_", "-").lstrip("/")
                        if clean_d and clean_d != name and clean_d not in references:
                            references.append(clean_d)

            stages.extend(extract_stages_from_skill_md(body))
            anti_patterns.extend(extract_anti_patterns(body))
            references.extend(extract_references(body, exclude_self=name))

        if card_file.exists():
            card_text = card_file.read_text(encoding="utf-8", errors="ignore")
            card_meta = extract_ascii_card(card_text)

            if card_meta.get("name"):
                name = card_meta["name"]
            if card_meta.get("category"):
                category = card_meta["category"]
            if card_meta.get("version"):
                version = card_meta["version"]
            if card_meta.get("invocation"):
                invocation = card_meta["invocation"]
            if card_meta.get("triggers"):
                triggers.extend(card_meta["triggers"])
            if card_meta.get("target"):
                target = card_meta["target"]

            if not stages:
                stages.extend(extract_stages_from_card_table(card_text))

            invariants.extend(extract_invariants(card_text))

            if card_meta.get("requires"):
                references.extend(card_meta["requires"])

            references.extend(extract_references(card_text, exclude_self=name))

        if not triggers and description:
            raw_matches = re.findall(r'"([^"]+)"|\'([^\']+)\'', description)
            triggers = [
                (t[0] or t[1]).strip().strip('"').strip("'")
                for t in raw_matches
                if (t[0] or t[1])
            ]
            if not triggers:
                triggers = [name.replace("-", " ")]

        clean_triggers = list(dict.fromkeys(triggers))
        clean_refs = list(dict.fromkeys([r for r in references if r != name]))

        return SkillCardDefinition(
            name=name,
            category=category,
            invocation=invocation,
            triggers=clean_triggers,
            version=version,
            target=target or description,
            stages=stages,
            anti_patterns=anti_patterns,
            invariants=invariants,
            dependencies=clean_refs,
            knowledge_items=[],
            services=[],
            tools=[],
            card_path=str(card_file) if card_file.exists() else "",
            skill_path=str(skill_file) if skill_file.exists() else "",
        )

    @classmethod
    def scan_root(
        cls, root_path: Path, max_depth: int = 4
    ) -> dict[str, SkillCardDefinition]:
        """Scan a root directory for all valid skill folders, enforcing Rule 52 bounded traversal."""
        return scan_root_fn(root_path, max_depth=max_depth, parse_directory_fn=cls.parse_directory)

    # Legacy protected helpers for 100% test backward compatibility
    @staticmethod
    def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        return extract_frontmatter(content)

    @staticmethod
    def _extract_ascii_card(content: str) -> dict[str, Any]:
        return extract_ascii_card(content)

    @staticmethod
    def _extract_stages_from_skill_md(body: str) -> list[SkillStageDefinition]:
        return extract_stages_from_skill_md(body)

    @staticmethod
    def _extract_stages_from_card_table(content: str) -> list[SkillStageDefinition]:
        return extract_stages_from_card_table(content)

    @staticmethod
    def _extract_anti_patterns(body: str) -> list[SkillAntiPatternDefinition]:
        return extract_anti_patterns(body)

    @staticmethod
    def _extract_invariants(content: str) -> list[SkillInvariantDefinition]:
        return extract_invariants(content)

    @staticmethod
    def _extract_references(text: str, exclude_self: str = "") -> list[str]:
        return extract_references(text, exclude_self=exclude_self)
