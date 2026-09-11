"""Contract test suite for legacy-modernization-pipeline meta-skill."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "legacy-modernization-pipeline"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestLegacyModernizationPipelineStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "legacy-modernization-pipeline"
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
class TestModernizationOrchestratorDriver:
    """Validate slotted domain entities and orchestrator execution driver."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from modernization_orchestrator import ModernizationPlanReport, ModernizationStageResult

        stage = ModernizationStageResult(
            stage_num=1,
            stage_name="Multi-Axis Audit",
            passed=True,
            duration_ms=5.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = ModernizationPlanReport(
            codebase_path="/tmp/legacy",
            target_module="billing",
            passed=True,
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_orchestrator_pipeline_stages(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert orchestrator pipeline executes and validates stages correctly."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from modernization_orchestrator import LegacyModernizationOrchestrator

        target = tmp_path / "legacy_app"
        target.mkdir()
        (target / "app.py").write_text("print('legacy')\n", encoding="utf-8")

        test_suite = tmp_path / "test_suite.py"
        test_suite.write_text("def test_legacy(): pass\n", encoding="utf-8")

        orchestrator = LegacyModernizationOrchestrator(workspace_root=tmp_path, target_module="legacy_app")
        report = orchestrator.execute_pipeline(test_suite_path=test_suite, changed_files=["app.py"])

        assert report.passed is True
        assert report.total_stages == 5
        assert report.passed_stages_count == 5
