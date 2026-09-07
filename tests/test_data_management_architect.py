"""Unit and integration tests for data-management-architect skill, companion scripts, and Knowledge Items."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    index_skill_catalog,
    query_skill_router,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

# Import companion scripts
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".agents" / "skills" / "data-management-architect"))
from scripts.data_contract_validator import DataContractValidator
from scripts.data_quality_profiler import DataQualityProfiler
from scripts.golden_record_resolver import (
    EntityRecord,
    GoldenRecordResolver,
    SurvivorshipRule,
)
from scripts.maturity_assessor import MaturityAssessor


@pytest.mark.unit
class TestDataManagementArchitectSkillStructure:
    """Validate skill files against deep-module craft standards and invariants."""

    @property
    def skill_dir(self) -> Path:
        return Path(__file__).parent.parent / ".agents" / "skills" / "data-management-architect"

    def test_skill_validator_passes_cleanly(self) -> None:
        """Assert SkillValidator passes cleanly with report.valid is True."""
        assert self.skill_dir.exists(), "Skill directory does not exist"
        report = SkillValidator.validate(self.skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        for check in report.checks:
            assert check.passed is True, f"Rule check failed: {check.name} - {check.message}"

    def test_card_md_single_pipe_ascii_and_schema(self) -> None:
        """Assert CARD.md satisfies Rule 37 single-pipe borders and header tags."""
        card_file = self.skill_dir / "CARD.md"
        assert card_file.exists()
        text = card_file.read_text(encoding="utf-8")

        # Must have SKILL: data-management-architect
        assert "SKILL:       data-management-architect" in text
        # Must have single-pipe border characters (Rule 37)
        assert "│" in text
        assert "║" not in text, "CARD.md should use single-pipe border '│' per Rule 37"
        # Must have stage progression table
        assert "| Stage | Objective |" in text

    def test_skill_md_anti_patterns_and_pillars(self) -> None:
        """Assert SKILL.md has exact anti-patterns formatting and core pillars."""
        skill_file = self.skill_dir / "SKILL.md"
        assert skill_file.exists()
        text = skill_file.read_text(encoding="utf-8")

        # Frontmatter
        assert "name: data-management-architect" in text
        # Exact Anti-Patterns heading
        assert "## Anti-Patterns" in text
        # Anti-pattern list format: - **Name** — Description
        assert "- **The Passive Data Swamp** —" in text
        assert "- **Uncontracted Producer Drift** —" in text
        assert "- **Fragmented Identity & Split Brain** —" in text
        assert "- **Post-Mortem Quality Inspection** —" in text

    def test_skill_parser_and_invariants(self) -> None:
        """Assert SkillCardParser extracts valid stages, anti-patterns, and blocking invariants."""
        node = SkillCardParser.parse_directory(self.skill_dir)
        assert node is not None
        assert node.name == "data-management-architect"
        assert len(node.stages) >= 5, f"Expected 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected >= 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants), "All checklist invariants must be blocking"


@pytest.mark.unit
class TestDataContractValidatorScript:
    """Test data_contract_validator.py against mock Open Data Contracts."""

    @pytest.fixture
    def contract_def(self) -> dict:
        return {
            "name": "mobility_trip_events",
            "version": "1.2.0",
            "schema": {
                "fields": {
                    "trip_id": {"type": "string", "required": True, "nullable": False},
                    "student_reference": {"type": "string", "required": True, "pattern": r"^ALU-\d{4}-\d{4}$"},
                    "price_euros": {"type": "float", "minimum": 0.0, "maximum": 500.0},
                    "status": {"type": "string", "enum": ["requested", "completed", "cancelled"]},
                    "event_timestamp": {"type": "timestamp", "required": True},
                }
            },
            "sla": {
                "freshness_field": "event_timestamp",
                "max_latency_hours": 48.0,
            },
        }

    def test_valid_dataset_passes(self, contract_def: dict) -> None:
        validator = DataContractValidator.from_dict(contract_def)
        valid_records = [
            {
                "trip_id": "TRIP-001",
                "student_reference": "ALU-2026-8942",
                "price_euros": 24.50,
                "status": "completed",
                "event_timestamp": "2026-09-06T12:00:00Z",
            }
        ]
        report = validator.validate_dataset(valid_records)
        assert report.is_compliant is True
        assert report.valid_records == 1
        assert report.quarantine_count == 0
        assert len(report.violations) == 0

    def test_invalid_records_detected(self, contract_def: dict) -> None:
        validator = DataContractValidator.from_dict(contract_def)
        bad_records = [
            {
                "trip_id": None,  # null violation
                "student_reference": "invalid_id_format",  # pattern mismatch
                "price_euros": 999.0,  # exceeds maximum 500.0
                "status": "unknown_status",  # enum violation
                "event_timestamp": "not_a_timestamp",  # type mismatch
            }
        ]
        report = validator.validate_dataset(bad_records, max_quarantine_ratio=0.0)
        assert report.is_compliant is False
        assert report.quarantine_count == 1
        assert len(report.violations) >= 4


@pytest.mark.unit
class TestDataQualityProfilerScript:
    """Test data_quality_profiler.py 6-dimension evaluation."""

    def test_profiler_computes_6_dimensions(self) -> None:
        profiler = DataQualityProfiler(
            key_fields=["trip_id"],
            required_fields=["trip_id", "student_id", "fare"],
            accuracy_ranges={"fare": (0.0, 300.0)},
            validation_rules={"student_id": {"pattern": r"^ALU-\d{4}-\d{4}$"}},
            timeliness_field="created_at",
            max_latency_hours=72.0,
        )

        test_records = [
            {"trip_id": "T1", "student_id": "ALU-2026-0001", "fare": 15.0, "created_at": "2026-09-06T10:00:00Z"},
            {"trip_id": "T2", "student_id": "ALU-2026-0002", "fare": 25.0, "created_at": "2026-09-06T11:00:00Z"},
            {"trip_id": "T3", "student_id": "ALU-2026-0003", "fare": 35.0, "created_at": "2026-09-06T12:00:00Z"},
        ]

        scorecard = profiler.profile(test_records, dataset_name="mobility_sample")
        assert scorecard.total_rows == 3
        assert scorecard.passed is True
        assert scorecard.overall_score >= 95.0

        # Check all 6 dimensions exist
        assert set(scorecard.dimensions.keys()) == {
            "accuracy", "completeness", "consistency", "timeliness", "validity", "uniqueness"
        }
        assert scorecard.dimensions["uniqueness"].score == 100.0
        assert scorecard.dimensions["completeness"].score == 100.0

    def test_profiler_detects_duplicates_and_nulls(self) -> None:
        profiler = DataQualityProfiler(
            key_fields=["trip_id"],
            required_fields=["trip_id", "student_id"],
        )

        bad_records = [
            {"trip_id": "T1", "student_id": "ALU-001"},
            {"trip_id": "T1", "student_id": "ALU-001"},  # duplicate
            {"trip_id": "T2", "student_id": None},       # null
        ]

        scorecard = profiler.profile(bad_records)
        assert scorecard.dimensions["uniqueness"].score < 100.0
        assert scorecard.dimensions["completeness"].score < 100.0


@pytest.mark.unit
class TestGoldenRecordResolverScript:
    """Test golden_record_resolver.py entity resolution and survivorship rules."""

    def test_golden_record_resolution(self) -> None:
        records = [
            EntityRecord(
                record_id="reg_01",
                source_system="registrar_system",
                updated_at="2026-01-10T10:00:00Z",
                attributes={
                    "student_id": "ALU-2026-8942",
                    "national_id": "FR-987654321",
                    "full_name": "Amélie Dubois",
                    "program": "Master in Artificial Intelligence",
                },
            ),
            EntityRecord(
                record_id="mob_99",
                source_system="mobility_portal",
                updated_at="2026-03-09T08:00:00Z",
                attributes={
                    "student_id": "ALU-2026-8942",
                    "national_id": "FR-987654321",
                    "full_name": "Amelie Dubois",
                    "campus_distance_km": 18.2,
                    "rideshare_benefit_approved": True,
                },
            ),
        ]

        resolver = GoldenRecordResolver(
            match_keys=["national_id", "student_id"],
            survivorship_rules={
                "full_name": SurvivorshipRule.SOURCE_PRIORITY,
                "campus_distance_km": SurvivorshipRule.MOST_RECENT,
            },
            source_priority=["registrar_system", "mobility_portal"],
        )

        goldens = resolver.resolve(records)
        assert len(goldens) == 1
        golden = goldens[0]

        assert golden.source_records_count == 2
        # full_name should survive from registrar_system (Amélie with accent)
        assert golden.resolved_attributes["full_name"] == "Amélie Dubois"
        assert golden.attribute_lineage["full_name"] == "registrar_system"
        # campus_distance_km should be populated from mobility_portal
        assert golden.resolved_attributes["campus_distance_km"] == 18.2
        assert golden.attribute_lineage["campus_distance_km"] == "mobility_portal"


@pytest.mark.unit
class TestMaturityAssessorScript:
    """Test maturity_assessor.py 5-level maturity scoring."""

    def test_maturity_assessment_and_roadmap(self) -> None:
        assessor = MaturityAssessor(target_level=4)
        scores = {
            "data_governance": 2,
            "data_architecture": 3,
            "data_modeling": 3,
            "data_quality": 2,
            "data_security_privacy": 4,
            "data_engineering_ops": 2,
        }

        report = assessor.evaluate_answers(scores, organization_name="Test University")
        assert report.target_maturity_level == 4
        assert 2.0 <= report.overall_maturity_level <= 3.0
        assert report.dimension_scores["data_governance"].gap == 2
        assert report.dimension_scores["data_security_privacy"].gap == 0
        assert len(report.prioritized_roadmap) > 0


@pytest.mark.unit
class TestSollaKnowledgeVault:
    """Validate canonical dual-file Knowledge Vault items (Rule 40)."""

    @property
    def vault_dir(self) -> Path:
        return Path(__file__).parent.parent / ".harness" / "knowledge"

    @pytest.mark.parametrize("ki_id", [
        "ki_solla_dikw_data_asset_continuum",
        "ki_solla_dmbok_governance_decision_rights",
        "ki_solla_contract_first_medallion_lakehouse",
        "ki_solla_six_dimension_quality_observability",
    ])
    def test_canonical_dual_file_ki_format(self, ki_id: str) -> None:
        """Assert each KI strictly adheres to metadata.json + summary.md (Rule 40)."""
        ki_path = self.vault_dir / ki_id
        assert ki_path.exists() and ki_path.is_dir(), f"KI directory missing: {ki_path}"

        meta_path = ki_path / "metadata.json"
        summary_path = ki_path / "summary.md"
        assert meta_path.exists(), f"Missing metadata.json in {ki_id}"
        assert summary_path.exists(), f"Missing summary.md in {ki_id}"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["id"] == ki_id
        assert bool(meta.get("title"))
        assert bool(meta.get("category"))
        assert isinstance(meta.get("tags"), list) and len(meta["tags"]) > 0
        assert isinstance(meta.get("provenance"), list) and len(meta["provenance"]) > 0
        assert bool(meta.get("source_repo"))

        summary_text = summary_path.read_text(encoding="utf-8")
        assert f"**ID:** `{ki_id}`" in summary_text
        assert "## Executive Summary" in summary_text
        assert len(summary_text) > 400


@pytest.mark.unit
class TestSkillKnowledgeGraphIntegration:
    """Verify registration and query resolution in the Skill Knowledge Graph."""

    def test_skill_indexed_and_queried(self) -> None:
        summary = index_skill_catalog()
        assert summary.get("status") == "ok"
        assert summary.get("total_nodes", 0) >= 10

        # Query semantic triggers
        res = query_skill_router("enterprise data management governance lakehouse", top_k=5)
        assert res.get("status") == "ok"
        matches = res.get("matches", [])
        assert len(matches) > 0

        # Rule 35: match entries are strictly keyed by 'skill_name'
        skill_names = [m.get("skill_name") or m.get("name") for m in matches]
        assert "data-management-architect" in skill_names
