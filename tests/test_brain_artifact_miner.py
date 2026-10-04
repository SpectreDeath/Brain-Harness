"""Comprehensive unit and contract tests for brain-artifact-miner skill.

Verifies:
1. SkillValidator compliance with zero errors and zero warnings (Rule 34)
2. SkillCardParser schema compliance (5 stages, anti-patterns, Rule 37 invariants)
3. Zero-fork configuration baseline schema (Rule 44)
4. Domain engine interface contracts, AST classification, and slotted/frozen immutability (Rule 12, Rule 43)
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

SKILL_DIR = Path(".agents/skills/brain-artifact-miner")
KV_DIR = Path(".harness/knowledge/ki_brain_20261003_01")


@pytest.mark.unit
class TestBrainArtifactMinerSkill:
    """Contract tests for brain-artifact-miner skill packaging."""

    def test_skill_directory_exists(self) -> None:
        assert SKILL_DIR.exists()
        assert (SKILL_DIR / "SKILL.md").exists()
        assert (SKILL_DIR / "CARD.md").exists()
        assert (SKILL_DIR / "config.default.yaml").exists()
        assert (SKILL_DIR / "scripts" / "brain_artifact_miner.py").exists()

    def test_skill_validator_passes_zero_warnings(self) -> None:
        """Verify SkillValidator passes with report.valid == True, 0 errors, 0 warnings (Rule 34)."""
        report = SkillValidator.validate_sync(SKILL_DIR)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        assert len(report.errors) == 0, f"Expected 0 errors: {report.errors}"
        assert len(report.warnings) == 0, f"Expected 0 warnings: {report.warnings}"

    def test_skill_card_parser_contract(self) -> None:
        """Verify SkillCardParser extracts 5 stages, anti-patterns, and blocking invariants."""
        node = SkillCardParser.parse_directory(SKILL_DIR)
        assert node is not None
        assert node.name == "brain-artifact-miner"
        assert len(node.stages) == 5
        assert len(node.anti_patterns) >= 7
        assert len(node.invariants) >= 6
        assert all(inv.is_blocking for inv in node.invariants)
        for expected_dep in ("book-to-skill-forge", "conversation-trajectory-miner", "epistemic-memory-lifecycle"):
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
            "byte_offset_indexing",
            "defensive_exception_logging",
            "default_brain_path",
        }
        for k in required_keys:
            assert k in config, f"Missing required config key: {k}"

    def test_engine_interface_and_slotted_immutability(self) -> None:
        """Verify engine exports, dataclasses, and immutability (Rule 12, Rule 43)."""
        import importlib.util
        import sys

        script_path = SKILL_DIR / "scripts" / "brain_artifact_miner.py"
        spec = importlib.util.spec_from_file_location("brain_artifact_miner", str(script_path))
        assert spec is not None and spec.loader is not None
        miner = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = miner
        spec.loader.exec_module(miner)

        # Verify exported functions
        for fn_name in ("build_offset_index", "scan_scratch_tools", "triage_task_logs", "generate_html_brief"):
            assert hasattr(miner, fn_name)
            assert callable(getattr(miner, fn_name))

        # Test ScratchCatalogItem & ScratchCatalog
        item = miner.ScratchCatalogItem(
            category="ast_and_lint",
            path="lint_test.py",
            functions=["lint_code"],
            imports=["ast"],
            docstring="Lint helper.",
        )
        catalog = miner.ScratchCatalog(
            total_scanned=1,
            classified_count=1,
            items_by_category={"ast_and_lint": [item]},
        )
        assert catalog.total_scanned == 1

        # Direct assignment immutability assertion (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            catalog.total_scanned = 5

        # Test HTML brief generation (Rule 51)
        brief = miner.generate_html_brief({
            "title": "Brief",
            "total_dirs": 5,
            "scratch_count": 10,
            "task_count": 2,
            "failed_tasks": 0,
            "categories": {"ast_and_lint": [item]},
        })
        assert "<!DOCTYPE html>" in brief
        assert "mermaid.initialize({" in brief

    def test_knowledge_vault_canonical_item(self) -> None:
        """Verify Knowledge Vault item dual-file format and isnad claims (Rule 40, Rule 41)."""
        assert KV_DIR.exists()
        meta_file = KV_DIR / "metadata.json"
        summary_file = KV_DIR / "summary.md"
        assert meta_file.exists()
        assert summary_file.exists()

        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["id"] == "ki_brain_20261003_01"
        assert data["isnad"]["status"] == "VERIFIED"
        assert len(data["isnad"]["claims"]) >= 2
        for claim in data["isnad"]["claims"]:
            assert "assertion" in claim
            assert "lineage" in claim
            assert len(claim["lineage"]) >= 1

    def test_skill_graph_discovery_and_indexing(self) -> None:
        """Verify skill graph indexing includes brain-artifact-miner (Rule 35, Rule 55)."""
        summary = index_skills_cmd(".")
        assert summary["indexed_skills"] >= 109
        registry = get_skill_registry(".")
        node = registry.get_skill("brain-artifact-miner")
        assert node is not None
        assert node.name == "brain-artifact-miner"
