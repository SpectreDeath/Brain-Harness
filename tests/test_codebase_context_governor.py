"""Contract test suite for codebase-context-governor meta-skill."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "codebase-context-governor"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestCodebaseContextGovernorStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "codebase-context-governor"
        assert len(node.stages) >= 5, f"Expected >= 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected >= 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants), "All invariants must be blocking"

    def test_frontmatter_budget_and_negative_boundary(self, skill_dir: Path) -> None:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists()
        text = skill_file.read_text(encoding="utf-8")

        # Rule 44: Description bounded between 100 and 350 chars with action verbs and negative boundary
        frontmatter, _ = SkillCardParser._extract_frontmatter(text)
        desc = frontmatter.get("description", "")
        assert 100 <= len(desc) <= 350, f"Description length {len(desc)} not in [100, 350]"
        assert "Do not use for" in desc, "Description must contain explicit negative boundary ('Do not use for...')"


@pytest.mark.unit
class TestContextGovernanceDriver:
    """Validate slotted domain entities, smell detection, and compute assessment."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from context_governance_driver import ContextGovernanceReport, ContextSmellViolation, GovernanceStageResult

        violation = ContextSmellViolation(
            rule_name="Test Rule",
            file_path="AGENTS.md",
            line_number=10,
            message="Test message",
            severity="WARNING",
        )
        with pytest.raises((AttributeError, TypeError)):
            violation.severity = "ERROR"  # type: ignore

        stage = GovernanceStageResult(
            stage_num=1,
            stage_name="Test Stage",
            passed=True,
            duration_ms=4.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = ContextGovernanceReport(
            workspace_root="/tmp/repo",
            passed=True,
            recommended_tier="High",
            stages=(stage,),
            violations=(violation,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_audit_smells_detects_bloat(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert smell auditor flags files exceeding 150 lines (Rule 11)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from context_governance_driver import ContextGovernanceDriver

        driver = ContextGovernanceDriver(tmp_path)
        bloated_file = tmp_path / "AGENTS.md"
        bloated_file.write_text("\n".join(f"Line {i}" for i in range(160)), encoding="utf-8")

        res, violations = driver.audit_smells(bloated_file)
        assert res.passed is False
        assert any(v.rule_name == "Instruction Line Budget" for v in violations)

    def test_dynamic_compute_assessment_routing(self, skill_dir: Path) -> None:
        """Assert 5D complexity score routes to proper compute tier (Rule 25)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from context_governance_driver import ContextGovernanceDriver

        driver = ContextGovernanceDriver(".")
        _, tier_high = driver.assess_compute_tier(0.85)
        assert tier_high == "High"

        _, tier_med = driver.assess_compute_tier(0.50)
        assert tier_med == "Medium"

        _, tier_low = driver.assess_compute_tier(0.20)
        assert tier_low == "Low"
