"""Contract test suite for multimedia-intelligence-forge meta-skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "multimedia-intelligence-forge"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestMultimediaIntelligenceForgeStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "multimedia-intelligence-forge"
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
class TestMultimediaDistillerDriver:
    """Validate slotted domain entities, dual-lens extraction, and dual-file vault scaffolding."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from multimedia_distiller import DistillationClaim, DistillationPlanReport, DistillationStageResult

        claim = DistillationClaim(
            claim_id="c1",
            assertion="Dual-lens extraction guarantees purity.",
            quote="Separate beliefs from actions.",
            timestamp_seconds=124.5,
        )
        with pytest.raises((AttributeError, TypeError)):
            claim.verified = False  # type: ignore

        stage = DistillationStageResult(
            stage_num=1,
            stage_name="Transcript Ingestion",
            passed=True,
            duration_ms=10.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = DistillationPlanReport(
            media_source="https://youtube.com/watch?v=sample",
            target_skill_name="sample-skill",
            sha256_hash="abcdef",
            passed=True,
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_distiller_dual_file_vault_commit(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert Rule 40 dual-file directory format in commit_knowledge_vault."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from multimedia_distiller import DistillationClaim, MultimediaDistillerEngine

        engine = MultimediaDistillerEngine("https://example.com/lecture", "lecture-skill")
        claims = [
            DistillationClaim(
                claim_id="c_101",
                assertion="Epistemic models form foundational truth.",
                quote="We must record what we believe.",
                timestamp_seconds=45.0,
            )
        ]

        out_dir = engine.commit_knowledge_vault(
            vault_root=tmp_path / "vault",
            ki_id="ki_lecture_101",
            title="Lecture Mental Models",
            sha256_hash="0123456789abcdef",
            claims=claims,
        )

        assert out_dir.is_dir()
        assert (out_dir / "metadata.json").exists()
        assert (out_dir / "summary.md").exists()

        meta = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta["id"] == "ki_lecture_101"
        assert meta["sha256"] == "0123456789abcdef"
        assert len(meta["claims"]) == 1

    def test_distiller_stage_validations(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert distiller stage handling for valid and invalid inputs."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from multimedia_distiller import DistillationClaim, MultimediaDistillerEngine

        engine = MultimediaDistillerEngine("source_test", "test-skill")

        # Missing transcript
        s1, sha = engine.ingest_and_hash_transcript(tmp_path / "missing.txt")
        assert s1.passed is False

        # Valid transcript
        valid_file = tmp_path / "transcript.txt"
        valid_file.write_text("Spoken lecture words here.", encoding="utf-8")
        s1_ok, sha_ok = engine.ingest_and_hash_transcript(valid_file)
        assert s1_ok.passed is True
        assert len(sha_ok) == 64

        # Dual-lens with claims
        s2 = engine.run_dual_lens_distillation([
            DistillationClaim("c1", "Assertion", "Quote", 10.0)
        ])
        assert s2.passed is True
