"""Contract test suite for external-repo-bridge-forge meta-skill."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "external-repo-bridge-forge"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestExternalRepoBridgeForgeStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "external-repo-bridge-forge"
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
class TestBridgeForgeDriver:
    """Validate slotted domain entities, Diátaxis generation, and C4 Mermaid models."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from bridge_forge_driver import BridgeForgeReport, BridgeRepoProfile, BridgeStageResult

        profile = BridgeRepoProfile(
            repo_url_or_path="https://github.com/example/tool",
            manifest_type="python",
            entrypoint_symbols=("execute",),
        )
        with pytest.raises((AttributeError, TypeError)):
            profile.manifest_type = "rust"  # type: ignore

        stage = BridgeStageResult(
            stage_num=1,
            stage_name="Repository Introspection",
            passed=True,
            duration_ms=8.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = BridgeForgeReport(
            repo_target="https://github.com/example/tool",
            plugin_name="example-plugin",
            passed=True,
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_repo_inspection_and_manifest_detection(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert repo inspector detects Python pyproject.toml correctly."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from bridge_forge_driver import ExternalRepoBridgeForgeDriver

        repo_dir = tmp_path / "sample_repo"
        repo_dir.mkdir()
        (repo_dir / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")

        driver = ExternalRepoBridgeForgeDriver(str(repo_dir), "sample-plugin")
        stage, profile = driver.inspect_repo(repo_dir)

        assert stage.passed is True
        assert profile.manifest_type == "python"

    def test_diataxis_suite_generation(self, tmp_path: Path, skill_dir: Path) -> None:
        """Assert driver authors all 4 Diátaxis quadrants plus llms.txt."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from bridge_forge_driver import ExternalRepoBridgeForgeDriver

        driver = ExternalRepoBridgeForgeDriver("source", "my-plugin")
        docs_dir = tmp_path / "docs"
        stage, docs = driver.generate_diataxis_suite(docs_dir)

        assert stage.passed is True
        assert (docs_dir / "tutorial.md").exists()
        assert (docs_dir / "how-to.md").exists()
        assert (docs_dir / "reference.md").exists()
        assert (docs_dir / "explanation.md").exists()
        assert (docs_dir / "llms.txt").exists()

    def test_c4_model_generation(self, skill_dir: Path) -> None:
        """Assert driver generates C4 Mermaid diagram."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from bridge_forge_driver import ExternalRepoBridgeForgeDriver

        driver = ExternalRepoBridgeForgeDriver("source", "my-plugin")
        stage, c4 = driver.generate_c4_model()

        assert stage.passed is True
        assert "C4Context" in c4
        assert "my-plugin" in c4
        assert "Subprocess Worker" in c4
