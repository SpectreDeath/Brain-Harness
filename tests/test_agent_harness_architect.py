"""Test suite for agent-harness-architect skill and Knowledge Vault item."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestAgentHarnessArchitectSkill:
    """Validate craft standards, frontmatter bounds, and card formatting."""

    @pytest.fixture
    def skill_dir(self) -> Path:
        p = (
            Path(__file__).parent.parent
            / ".agents"
            / "skills"
            / "agent-harness-architect"
        )
        assert p.exists(), f"Skill directory missing: {p}"
        return p

    @pytest.fixture
    def ki_dir(self) -> Path:
        p = (
            Path(__file__).parent.parent
            / ".harness"
            / "knowledge"
            / "ki_self_20260917_01"
        )
        assert p.exists(), f"Knowledge Item directory missing: {p}"
        return p

    def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = SkillValidator.validate_sync(skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        # Assert zero warnings on pillars
        assert len(report.warnings) == 0, (
            f"Unexpected warnings in report: {report.warnings}"
        )

    def test_frontmatter_description_bounds(self, skill_dir: Path) -> None:
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+)$", skill_text, re.MULTILINE)
        assert m is not None, "Missing description in frontmatter"
        desc = m.group(1).strip()
        assert 100 <= len(desc) <= 350, (
            f"Description length {len(desc)} not in [100, 350] (Rule 44)"
        )
        assert desc.startswith(("Architect", "Implement", "Audit", "Design")), (
            "Description must start with action verb"
        )
        assert "Do not use for" in desc, (
            "Description must state explicit negative boundary (Rule 44)"
        )

    def test_card_ascii_formatting_and_pillars(self, skill_dir: Path) -> None:
        card_text = (skill_dir / "CARD.md").read_text(encoding="utf-8")
        # Rule 37: Single-pipe borders, not double borders
        assert "│" in card_text, "CARD.md must use single-pipe borders (Rule 37)"
        assert "║" not in card_text, "CARD.md must not use double borders (Rule 37)"
        assert (
            "SKILL:       agent-harness-architect" in card_text
            or "SKILL: agent-harness-architect" in card_text
        )

        # Parse via SkillCardParser
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "agent-harness-architect"
        assert len(node.stages) == 5, f"Expected 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, (
            f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        )

    def test_zero_fork_config(self, skill_dir: Path) -> None:
        config_path = skill_dir / "config.default.yaml"
        assert config_path.exists(), "Missing config.default.yaml (Rule 44)"
        text = config_path.read_text(encoding="utf-8")
        assert "operational_budgets" in text
        assert "max_turns" in text

    def test_knowledge_vault_dual_file_format(self, ki_dir: Path) -> None:
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "Missing metadata.json (Rule 40)"
        assert summary_file.exists(), "Missing summary.md (Rule 40)"

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki_self_20260917_01"
        assert meta["category"] == "agent_orchestration"
        assert "isnad" in meta
        assert "claims" in meta["isnad"]
        assert len(meta["isnad"]["claims"]) >= 3
        for claim in meta["isnad"]["claims"]:
            assert "assertion" in claim
            assert "source" in claim
            assert claim.get("verified") is True

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Five-Part Agent Harness Architecture" in summary_text
        assert "Four Reliability Mechanisms" in summary_text
        assert "Four-Layer Solution Stack" in summary_text
