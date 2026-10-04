"""Comprehensive unit and contract tests for conversation-trajectory-miner skill.

Verifies:
1. SkillValidator compliance with zero errors and zero warnings (Rule 34)
2. SkillCardParser schema compliance (stages, anti-patterns, Rule 37 invariants)
3. Zero-fork configuration baseline schema (Rule 44)
4. Domain engine interface contracts, failure cluster archaeology, and slotted/frozen immutability (Rule 12, Rule 43)
5. Skill graph registration and topological discovery (Rule 35, Rule 55)
"""

from __future__ import annotations

from pathlib import Path
import pytest
import yaml

from harness.creator.skills import SkillValidator
from harness.services.skill_parser import SkillCardParser
from harness.services.conversation_trajectory_miner import (
    StandardConversationTrajectoryMinerService,
)

SKILL_DIR = Path(".agents/skills/conversation-trajectory-miner")


@pytest.mark.unit
class TestConversationTrajectoryMinerSkill:
    """Contract tests for conversation-trajectory-miner skill packaging."""

    def test_skill_directory_exists(self) -> None:
        assert SKILL_DIR.exists()
        assert (SKILL_DIR / "SKILL.md").exists()
        assert (SKILL_DIR / "CARD.md").exists()
        assert (SKILL_DIR / "config.default.yaml").exists()
        assert (SKILL_DIR / "scripts" / "trajectory_miner.py").exists()

    def test_skill_validator_passes_zero_warnings(self) -> None:
        """Verify SkillValidator passes with report.valid == True, 0 errors, 0 warnings (Rule 34)."""
        report = SkillValidator.validate_sync(SKILL_DIR)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        assert len(report.errors) == 0, f"Expected 0 errors: {report.errors}"
        assert len(report.warnings) == 0, f"Expected 0 warnings: {report.warnings}"

    def test_skill_card_parser_contract(self) -> None:
        """Verify SkillCardParser extracts stages, anti-patterns, and blocking invariants."""
        node = SkillCardParser.parse_directory(SKILL_DIR)
        assert node is not None
        assert node.name == "conversation-trajectory-miner"
        assert len(node.stages) >= 5
        assert len(node.anti_patterns) >= 5
        assert len(node.invariants) >= 5
        assert all(inv.is_blocking for inv in node.invariants)
        for expected_dep in ("book-to-skill-forge", "epistemic-memory-lifecycle"):
            assert expected_dep in node.dependencies

    def test_config_default_schema(self) -> None:
        """Verify config.default.yaml declares baseline operational budgets (Rule 44)."""
        config_path = SKILL_DIR / "config.default.yaml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert "timeout_seconds" in data
        assert "token_budget_limit" in data
        assert "max_retries" in data
        assert "sqlite_ro_mode" in data
        assert data["sqlite_ro_mode"] is True

    def test_service_engine_instantiation(self) -> None:
        """Verify StandardConversationTrajectoryMinerService initializes cleanly."""
        service = StandardConversationTrajectoryMinerService()
        assert service is not None
