"""Automated tests for orca-orchestrator skill hygiene, card parsing, and zero-fork config."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orca_orchestrator_skill_validation() -> None:
    """Verify that orca-orchestrator satisfies all SkillValidator rules."""
    skill_dir = Path(".agents/skills/orca-orchestrator")
    if not skill_dir.exists():
        skill_dir = (
            Path(__file__).parent.parent / ".agents" / "skills" / "orca-orchestrator"
        )

    report = await SkillValidator.validate_async(skill_dir)
    assert report.valid is True, f"Skill validation failed: {report.errors}"


@pytest.mark.unit
def test_orca_orchestrator_card_and_anti_patterns() -> None:
    """Verify CARD.md parsing, stages, anti-patterns, and invariants."""
    skill_dir = Path(".agents/skills/orca-orchestrator")
    if not skill_dir.exists():
        skill_dir = (
            Path(__file__).parent.parent / ".agents" / "skills" / "orca-orchestrator"
        )

    node = SkillCardParser.parse_directory(skill_dir)
    assert node is not None, "SkillCardParser failed to parse orca-orchestrator"
    assert node.name == "orca-orchestrator"
    assert len(node.stages) >= 4, f"Expected >= 4 stages, found {len(node.stages)}"
    assert len(node.anti_patterns) >= 3, (
        f"Expected >= 3 anti-patterns, found {len(node.anti_patterns)}"
    )
    assert len(node.invariants) >= 3, (
        f"Expected >= 3 invariants, found {len(node.invariants)}"
    )


@pytest.mark.unit
def test_orca_orchestrator_zero_fork_config() -> None:
    """Verify config.default.yaml operational budgets and schema (Rule 44)."""
    cfg_file = Path(".agents/skills/orca-orchestrator/config.default.yaml")
    if not cfg_file.exists():
        cfg_file = (
            Path(__file__).parent.parent
            / ".agents"
            / "skills"
            / "orca-orchestrator"
            / "config.default.yaml"
        )

    assert cfg_file.exists(), f"Missing config.default.yaml: {cfg_file}"
    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    assert "operational_budgets" in data
    assert data["operational_budgets"]["coordinator_check_timeout_ms"] > 0
    assert data["operational_budgets"]["keepalive_cadence_seconds"] == 15
    assert "codex" in data["supported_agents"]
    assert "claude" in data["supported_agents"]
