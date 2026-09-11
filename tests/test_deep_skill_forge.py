"""Contract test suite for deep-skill-forge meta-skill."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "deep-skill-forge"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestDeepSkillForgeStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "deep-skill-forge"
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
class TestPipelineRunnerAndKIScaffolder:
    """Validate bundled pipeline driver and Rule 40 dual-file Knowledge Item generator."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from pipeline_runner import PipelineStageResult, PipelineRunReport

        result = PipelineStageResult(
            stage_num=1,
            stage_name="Test Stage",
            passed=True,
            duration_ms=10.5,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            result.passed = False  # type: ignore

        report = PipelineRunReport(
            skill_name="test-skill",
            source_path="source.md",
            passed=True,
            stages=(result,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_knowledge_item_scaffolder_dual_file_format(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert Rule 40 canonical dual-file directory format."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from ki_scaffolder import IsnadClaim, KnowledgeItemScaffolder

        vault_dir = tmp_path / "knowledge_vault"
        scaffolder = KnowledgeItemScaffolder(vault_root=vault_dir)

        # Create dummy source
        source_file = tmp_path / "literature.md"
        source_file.write_text("# Primary Literature Source\nGround truth assertion.\n", encoding="utf-8")

        claim = IsnadClaim(
            claim_id="claim_001",
            assertion="Ground truth assertion.",
            evidence_quote="Ground truth assertion.",
            line_number=2,
        )

        out_dir = scaffolder.scaffold(
            ki_id="ki_test_literature",
            title="Test Literature Synthesis",
            source_path=source_file,
            category="meta-skills",
            claims=[claim],
        )

        assert out_dir.is_dir()
        assert out_dir.name == "ki_test_literature"

        meta_file = out_dir / "metadata.json"
        summary_file = out_dir / "summary.md"
        assert meta_file.exists(), "metadata.json must exist in dual-file format (Rule 40)"
        assert summary_file.exists(), "summary.md must exist in dual-file format (Rule 40)"

        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta_data["id"] == "ki_test_literature"
        assert meta_data["title"] == "Test Literature Synthesis"
        assert len(meta_data["sha256"]) == 64
        assert len(meta_data["claims"]) == 1
        assert meta_data["claims"][0]["claim_id"] == "claim_001"

    def test_pipeline_engine_source_and_package_verification(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert pipeline engine stage validations."""
        import sys
        sys.path.insert(0, str(skill_dir / "scripts"))
        from pipeline_runner import DeepSkillPipelineEngine

        # 1. Missing source fails Stage 1
        engine_bad = DeepSkillPipelineEngine(
            workspace_root=tmp_path,
            skill_name="my-skill",
            source_path=tmp_path / "nonexistent.md",
        )
        s1 = engine_bad.verify_source()
        assert s1.passed is False
        assert "missing" in s1.message.lower()

        # 2. Existing source passes Stage 1
        valid_source = tmp_path / "valid_source.md"
        valid_source.write_text("A" * 200, encoding="utf-8")
        engine_good = DeepSkillPipelineEngine(
            workspace_root=tmp_path,
            skill_name="my-skill",
            source_path=valid_source,
        )
        s1_good = engine_good.verify_source()
        assert s1_good.passed is True
