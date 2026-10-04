"""Comprehensive unit and contract tests for temp-artifact-miner skill.

Verifies:
1. SkillValidator compliance with zero errors and zero warnings (Rule 34)
2. SkillCardParser schema compliance (5 stages, anti-patterns, Rule 37 invariants)
3. Zero-fork configuration baseline schema (Rule 44)
4. Domain engine interface contracts, HTML parsing, heavy bounding, and slotted/frozen immutability (Rule 12, Rule 43)
5. Knowledge Vault dual-file format and isnad claim verification (Rule 40, Rule 41)
6. Skill graph registration and topological discovery (Rule 35, Rule 55)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml

from harness.creator.skills import SkillValidator
from harness.services.skill_parser import SkillCardParser
from harness.services.skill_graph import BuiltinSkillRegistryService
from harness.commands.skills import get_skill_registry, index_skills_cmd

SKILL_DIR = Path(".agents/skills/temp-artifact-miner")
KV_DIR = Path(".harness/knowledge/ki_temp_20261003_01")


@pytest.mark.unit
class TestTempArtifactMinerSkill:
    """Contract tests for temp-artifact-miner skill packaging."""

    def test_skill_directory_exists(self) -> None:
        assert SKILL_DIR.exists()
        assert (SKILL_DIR / "SKILL.md").exists()
        assert (SKILL_DIR / "CARD.md").exists()
        assert (SKILL_DIR / "config.default.yaml").exists()
        assert (SKILL_DIR / "scripts" / "temp_artifact_miner.py").exists()

    def test_skill_validator_passes_zero_warnings(self) -> None:
        """Verify SkillValidator passes with report.valid == True, 0 errors, 0 warnings (Rule 34)."""
        report = SkillValidator.validate_sync(SKILL_DIR)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        assert len(report.errors) == 0, f"Expected 0 errors: {report.errors}"
        assert len(report.warnings) == 0, f"Expected 0 warnings: {report.warnings}"

    def test_skill_card_parser_contract(self) -> None:
        """Verify SkillCardParser extracts 5 stages, anti-patterns, and blocking invariants (Rule 37)."""
        node = SkillCardParser.parse_directory(SKILL_DIR)
        assert node is not None
        assert node.name == "temp-artifact-miner"
        assert len(node.stages) == 5
        assert len(node.anti_patterns) >= 6
        assert len(node.invariants) >= 6
        assert all(inv.is_blocking for inv in node.invariants)
        for expected_dep in ("book-to-skill-forge", "brain-artifact-miner", "conversation-trajectory-miner", "epistemic-memory-lifecycle"):
            assert expected_dep in node.dependencies

    def test_config_default_schema(self) -> None:
        """Verify config.default.yaml declares baseline operational budgets (Rule 44)."""
        config_path = SKILL_DIR / "config.default.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        required_keys = {
            "timeout_seconds",
            "token_budget_limit",
            "max_retries",
            "max_scan_depth",
            "batch_size",
            "heavy_topology_byte_threshold",
            "defensive_exception_logging",
            "default_temp_path",
        }
        for k in required_keys:
            assert k in config, f"Missing required config key: {k}"

    def test_engine_interface_and_slotted_immutability(self) -> None:
        """Verify engine exports, dataclasses, and immutability (Rule 12, Rule 43)."""
        import importlib.util
        import sys

        script_path = SKILL_DIR / "scripts" / "temp_artifact_miner.py"
        spec = importlib.util.spec_from_file_location("temp_artifact_miner", str(script_path))
        assert spec is not None and spec.loader is not None
        miner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = miner
        spec.loader.exec_module(miner)

        # Verify exported functions
        for fn_name in ("scan_temp_briefs", "parse_html_brief", "triage_pytest_sandboxes", "tail_diagnostic_log", "generate_salvage_markdown"):
            assert hasattr(miner, fn_name)
            assert callable(getattr(miner, fn_name))

        # Test BriefCatalogItem & BriefCatalog
        item = miner.BriefCatalogItem(
            name="test-brief.html",
            path="C:/temp/test-brief.html",
            category="architecture-review",
            title="Test Architecture Brief",
            size_bytes=5000,
            mtime=1700000000.0,
            has_mermaid=True,
            has_scorecard=True,
            has_antipatterns=False,
            is_heavy_topology=False,
            mermaid_dags=["graph TD\n  A --> B"],
            sha256="abc123def456"
        )
        catalog = miner.BriefCatalog(
            total_scanned=1,
            brief_count=1,
            total_bytes=5000,
            heavy_count=0,
            items_by_category={"architecture-review": [item]},
        )
        assert catalog.total_scanned == 1
        assert catalog.brief_count == 1

        # Direct assignment immutability assertion (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            catalog.total_scanned = 10

        with pytest.raises((AttributeError, TypeError)):
            item.title = "Modified"

        # Test Markdown salvage generator
        md = miner.generate_salvage_markdown(catalog)
        assert "# Ephemeral Visual Brief Salvage Index" in md
        assert "architecture-review" in md

    def test_engine_html_parsing_and_heavy_bounding(self, tmp_path: Path) -> None:
        """Verify HTML brief parsing and heavy topology bounding (Rule 9, Rule 48)."""
        import importlib.util
        import sys

        script_path = SKILL_DIR / "scripts" / "temp_artifact_miner.py"
        spec = importlib.util.spec_from_file_location("temp_artifact_miner", str(script_path))
        assert spec is not None and spec.loader is not None
        miner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = miner
        spec.loader.exec_module(miner)

        # Create normal brief
        normal_file = tmp_path / "architecture-review-test.html"
        normal_content = """<!DOCTYPE html>
<html>
<head><title>Architecture Review: Sample</title></head>
<body>
  <div class="mermaid">graph LR\n  X --> Y</div>
  <table><tr><td>Evaluation Scorecard</td></tr></table>
  <section>Anti-Pattern Defense Matrix</section>
</body>
</html>"""
        normal_file.write_text(normal_content, encoding="utf-8")

        item_normal = miner.parse_html_brief(normal_file, heavy_threshold=50000)
        assert item_normal.name == "architecture-review-test.html"
        assert item_normal.category == "architecture-review"
        assert item_normal.title == "Architecture Review: Sample"
        assert item_normal.has_mermaid is True
        assert item_normal.has_scorecard is True
        assert item_normal.has_antipatterns is True
        assert item_normal.is_heavy_topology is False
        assert len(item_normal.mermaid_dags) == 1
        assert "X --> Y" in item_normal.mermaid_dags[0]

        # Create heavy brief exceeding threshold
        heavy_file = tmp_path / "skill-graph-huge.html"
        heavy_content = "<!DOCTYPE html><html><head><title>Huge Topology</title></head><body>" + ("x" * 60000) + "</body></html>"
        heavy_file.write_text(heavy_content, encoding="utf-8")

        item_heavy = miner.parse_html_brief(heavy_file, heavy_threshold=50000)
        assert item_heavy.category == "skill-graph"
        assert item_heavy.title == "Huge Topology"
        assert item_heavy.is_heavy_topology is True
        assert len(item_heavy.mermaid_dags) == 0  # Bounded; raw content not expanded

    def test_engine_sandbox_triage(self, tmp_path: Path) -> None:
        """Verify pytest sandbox inspection with bounded depth and noise pruning (Rule 52)."""
        import importlib.util
        import sys

        script_path = SKILL_DIR / "scripts" / "temp_artifact_miner.py"
        spec = importlib.util.spec_from_file_location("temp_artifact_miner", str(script_path))
        assert spec is not None and spec.loader is not None
        miner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = miner
        spec.loader.exec_module(miner)

        # Mock sandbox structure
        pytest_root = tmp_path / "pytest-of-spectre"
        run_dir = pytest_root / "pytest-999"
        fixture_dir = run_dir / "test_fixture_0"
        mock_skills = fixture_dir / "skills" / "mock-skill-a"
        mock_skills.mkdir(parents=True)

        report = miner.triage_pytest_sandboxes(tmp_path)
        assert report.total_runs == 1
        assert len(report.runs) == 1
        assert report.runs[0].name == "pytest-999"
        assert "mock-skill-a" in report.runs[0].mock_skills

    def test_knowledge_vault_canonical_item(self) -> None:
        """Verify Knowledge Vault item dual-file format and isnad claims (Rule 40, Rule 41)."""
        assert KV_DIR.exists()
        meta_file = KV_DIR / "metadata.json"
        summary_file = KV_DIR / "summary.md"
        assert meta_file.exists()
        assert summary_file.exists()

        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["id"] == "ki_temp_20261003_01"
        assert data["isnad"]["status"] == "VERIFIED"
        assert len(data["isnad"]["claims"]) >= 2
        for claim in data["isnad"]["claims"]:
            assert "assertion" in claim
            assert "lineage" in claim
            assert len(claim["lineage"]) >= 1

    def test_skill_graph_discovery_and_indexing(self) -> None:
        """Verify skill graph indexing includes temp-artifact-miner (Rule 35, Rule 55)."""
        summary = index_skills_cmd(".")
        assert summary["indexed_skills"] >= 110
        registry = get_skill_registry(".")
        node = registry.get_skill("temp-artifact-miner")
        assert node is not None
        assert node.name == "temp-artifact-miner"
