"""Automated unit and integration test contracts for neo4j-knowledge-graph-architect skill.

Verifies:
1. CypherLinter static safety gates (unbounded hops, trail semantics traps, MERGE mutations)
2. Slotted & frozen 7-tuple TemporalEvidenceObject & EvidenceBatch models
3. Neo4jBatchPipeline chunking and double-load idempotency simulation
4. Skill ecosystem registration and directory hygiene
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any
import pytest


def _load_module(module_name: str, rel_path: str) -> Any:
    """Load module from relative file path using importlib."""
    script_path = Path(rel_path).resolve()
    assert script_path.exists(), f"Script path missing: {script_path}"
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load modules dynamically from .agents/skills/neo4j-knowledge-graph-architect/scripts/
_linter_mod = _load_module(
    "neo4j_cypher_linter",
    ".agents/skills/neo4j-knowledge-graph-architect/scripts/cypher_linter.py",
)
_evidence_mod = _load_module(
    "neo4j_evidence_model",
    ".agents/skills/neo4j-knowledge-graph-architect/scripts/evidence_model.py",
)
_ingest_mod = _load_module(
    "neo4j_batch_ingest",
    ".agents/skills/neo4j-knowledge-graph-architect/scripts/batch_ingest.py",
)

CypherLinter = _linter_mod.CypherLinter
LintSeverity = _linter_mod.LintSeverity

TemporalEvidenceObject = _evidence_mod.TemporalEvidenceObject
EvidenceStatus = _evidence_mod.EvidenceStatus
EvidenceBoundaryLayer = _evidence_mod.EvidenceBoundaryLayer
EvidenceBatch = _evidence_mod.EvidenceBatch

Neo4jBatchPipeline = _ingest_mod.Neo4jBatchPipeline
BatchIngestConfig = _ingest_mod.BatchIngestConfig


@pytest.mark.unit
class TestCypherLinter:
    """Contract verification for CypherLinter static safety analysis."""

    def test_unbounded_traversal_detection(self) -> None:
        query = "MATCH (a:Person)-[:CITES*]->(b:Paper) RETURN a, b"
        report = CypherLinter.lint(query)
        assert not report.valid
        assert report.has_errors
        error_rules = [d.rule_id for d in report.diagnostics if d.severity == LintSeverity.ERROR]
        assert "CYPHER-001" in error_rules

    def test_bounded_traversal_allowed(self) -> None:
        query = "MATCH (a:Person {id: $id})-[:CITES*1..4]->(b:Paper) RETURN a, b"
        report = CypherLinter.lint(query)
        assert report.valid
        error_rules = [d.rule_id for d in report.diagnostics if d.severity == LintSeverity.ERROR]
        assert "CYPHER-001" not in error_rules

    def test_merge_mutation_detection(self) -> None:
        query = """
        UNWIND $batch AS row
        MERGE (p:Paper {doi: row.doi, updated_at: datetime()})
        RETURN p
        """
        report = CypherLinter.lint(query)
        assert not report.valid
        error_rules = [d.rule_id for d in report.diagnostics if d.severity == LintSeverity.ERROR]
        assert "CYPHER-002" in error_rules

    def test_isolated_merge_allowed(self) -> None:
        query = """
        UNWIND $batch AS row
        MERGE (p:Paper {doi: row.doi})
        ON CREATE SET p.created_at = datetime()
        ON MATCH SET p.updated_at = datetime()
        RETURN p
        """
        report = CypherLinter.lint(query)
        assert report.valid
        error_rules = [d.rule_id for d in report.diagnostics if d.severity == LintSeverity.ERROR]
        assert "CYPHER-002" not in error_rules

    def test_trail_semantics_warning_on_diamond(self) -> None:
        query = "MATCH (a:Node)-[:R1]->(b:Node)-[:R2]->(c:Node)<-[:R3]-(d:Node) RETURN a, c"
        report = CypherLinter.lint(query)
        warning_rules = [d.rule_id for d in report.diagnostics if d.severity == LintSeverity.WARNING]
        assert "CYPHER-003" in warning_rules

    def test_with_split_diamond_allowed(self) -> None:
        query = """
        MATCH (a:Node {id: $id})-[:R1]->(b:Node)
        WITH a, b
        MATCH (b)-[:R2]->(c:Node)
        RETURN a, b, c
        """
        report = CypherLinter.lint(query)
        warning_rules = [d.rule_id for d in report.diagnostics if d.rule_id == "CYPHER-003"]
        assert len(warning_rules) == 0

    def test_unparameterized_interpolation_warning(self) -> None:
        query = "MATCH (p:Person {name: '{name}'}) RETURN p"
        report = CypherLinter.lint(query)
        warning_rules = [d.rule_id for d in report.diagnostics if d.rule_id == "CYPHER-004"]
        assert len(warning_rules) > 0

    def test_empty_query_error(self) -> None:
        report = CypherLinter.lint("   ")
        assert not report.valid
        assert "CYPHER-000" in [d.rule_id for d in report.diagnostics]


@pytest.mark.unit
class TestTemporalEvidenceModel:
    """Contract verification for slotted 7-tuple TemporalEvidenceObject."""

    def test_evidence_object_creation_and_slots(self) -> None:
        obj = TemporalEvidenceObject(
            subject="doi:10.1000/182",
            predicate="INHIBITS",
            object="uniprot:P00533",
            time="2026-09-07T12:00:00Z",
            source="pubmed:3829102",
            confidence=0.92,
            status=EvidenceStatus.PEER_REVIEWED,
            boundary_layer=EvidenceBoundaryLayer.PRIMARY_FACT,
        )
        assert obj.subject == "doi:10.1000/182"
        assert obj.confidence == 0.92
        assert obj.status == EvidenceStatus.PEER_REVIEWED

        # Assert frozenness (FrozenInstanceError inherits from AttributeError in Python)
        with pytest.raises((AttributeError, TypeError)):
            obj.confidence = 0.5

    def test_confidence_bounds_validation(self) -> None:
        with pytest.raises(AssertionError):
            TemporalEvidenceObject(
                subject="s",
                predicate="p",
                object="o",
                time="2026-01-01",
                source="src",
                confidence=1.5,  # Invalid: > 1.0
                status=EvidenceStatus.HYPOTHESIS,
            )

    def test_empty_fields_validation(self) -> None:
        with pytest.raises(AssertionError):
            TemporalEvidenceObject(
                subject="",  # Invalid: empty
                predicate="p",
                object="o",
                time="2026-01-01",
                source="src",
                confidence=0.8,
                status=EvidenceStatus.HYPOTHESIS,
            )

    def test_derived_hypothesis_inferred_flag_auto_set(self) -> None:
        obj = TemporalEvidenceObject(
            subject="drug:123",
            predicate="PREDICTED_BINDING",
            object="target:456",
            time="2026-09-07",
            source="model:alphafold_v3",
            confidence=0.75,
            status=EvidenceStatus.HYPOTHESIS,
            boundary_layer=EvidenceBoundaryLayer.DERIVED_HYPOTHESIS,
        )
        assert obj.derived_metadata.get("inferred") is True

    def test_to_cypher_parameters_serialization(self) -> None:
        obj = TemporalEvidenceObject(
            subject="s1",
            predicate="p1",
            object="o1",
            time="2026-09-07",
            source="src1",
            confidence=0.85,
            status=EvidenceStatus.ACCEPTED,
        )
        params = obj.to_cypher_parameters()
        assert params["subject"] == "s1"
        assert params["confidence"] == 0.85
        assert params["status"] == "ACCEPTED"
        assert params["boundary_layer"] == "PRIMARY_FACT"
        assert "metadata_json" in params

    def test_evidence_batch_unwind_conversion(self) -> None:
        raw_list = [
            {"subject": "s1", "predicate": "p1", "object": "o1", "source": "src1", "confidence": 0.9},
            {"subject": "s2", "predicate": "p2", "object": "o2", "source": "src2", "confidence": 0.8},
        ]
        batch = EvidenceBatch.from_json_list(raw_list)
        assert batch.count == 2
        unwind_rows = batch.to_unwind_batch()
        assert len(unwind_rows) == 2
        assert unwind_rows[0]["subject"] == "s1"
        assert unwind_rows[1]["subject"] == "s2"


@pytest.mark.unit
class TestNeo4jBatchPipeline:
    """Contract verification for Neo4jBatchPipeline chunking and idempotency."""

    def test_dataset_chunking(self) -> None:
        pipeline = Neo4jBatchPipeline(config=BatchIngestConfig(chunk_size=10, dry_run=True))
        dataset = [{"id": i} for i in range(25)]
        chunks = pipeline.chunk_dataset(dataset)
        assert len(chunks) == 3
        assert len(chunks[0]) == 10
        assert len(chunks[1]) == 10
        assert len(chunks[2]) == 5

    def test_dry_run_ingestion(self) -> None:
        pipeline = Neo4jBatchPipeline(config=BatchIngestConfig(chunk_size=50, dry_run=True))
        dataset = [{"subject": f"s_{i}", "predicate": "REL", "object": f"o_{i}"} for i in range(120)]
        summary = pipeline.ingest_dataset(dataset)
        assert summary.total_records == 120
        assert summary.chunks_processed == 3
        assert summary.dry_run is True
        assert summary.nodes_created == 240
        assert summary.relationships_created == 120

    def test_double_load_idempotency_simulation(self) -> None:
        pipeline = Neo4jBatchPipeline(config=BatchIngestConfig(chunk_size=100, dry_run=True))
        dataset = [{"subject": "s1", "predicate": "REL", "object": "o1"}]
        # Dry run idempotency gate returns True
        result = pipeline.run_idempotency_gate(dataset)
        assert result is True

    def test_config_bounds(self) -> None:
        with pytest.raises(AssertionError):
            BatchIngestConfig(chunk_size=5)  # Invalid: < 10

        with pytest.raises(AssertionError):
            BatchIngestConfig(chunk_size=20000)  # Invalid: > 10000


@pytest.mark.unit
class TestSkillEcosystemIntegration:
    """Contract verification for skill files, directory hygiene, and CONTEXT-MAP.md."""

    def test_skill_directory_exists_and_contains_scripts(self) -> None:
        skill_dir = Path(".agents/skills/neo4j-knowledge-graph-architect")
        assert skill_dir.is_dir()
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "CARD.md").exists()
        assert (skill_dir / "REFERENCE.md").exists()
        assert (skill_dir / "scripts" / "cypher_linter.py").exists()
        assert (skill_dir / "scripts" / "evidence_model.py").exists()
        assert (skill_dir / "scripts" / "batch_ingest.py").exists()

    def test_context_map_registration(self) -> None:
        context_map = Path("CONTEXT-MAP.md").read_text(encoding="utf-8")
        assert "neo4j-knowledge-graph-architect" in context_map
        assert "Data Engineering" in context_map
