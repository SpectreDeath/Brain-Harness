"""Contract test suite for knowledge-graph-pipeline meta-skill."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "knowledge-graph-pipeline"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestKnowledgeGraphPipelineStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "knowledge-graph-pipeline"
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
class TestKnowledgeGraphPipelineDriver:
    """Validate slotted domain entities, Cypher query generation, and recursive SQL CTEs."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from graph_pipeline_driver import (
            GraphEntityNode,
            GraphPipelineReport,
            GraphPipelineStageResult,
            GraphRelationshipEdge,
        )

        node = GraphEntityNode(
            label="Customer",
            primary_key="cust_id",
            properties=("name", "tier"),
        )
        with pytest.raises((AttributeError, TypeError)):
            node.label = "Client"  # type: ignore

        rel = GraphRelationshipEdge(
            rel_type="PURCHASED",
            source_label="Customer",
            target_label="Product",
        )
        with pytest.raises((AttributeError, TypeError)):
            rel.rel_type = "BOUGHT"  # type: ignore

        stage = GraphPipelineStageResult(
            stage_num=1,
            stage_name="Data Discovery",
            passed=True,
            duration_ms=5.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = GraphPipelineReport(
            dataset_name="ecommerce_data",
            passed=True,
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_cypher_batch_ingest_query_generation(self, skill_dir: Path) -> None:
        """Assert generator creates valid idempotent UNWIND and MERGE queries."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from graph_pipeline_driver import KnowledgeGraphPipelineEngine

        engine = KnowledgeGraphPipelineEngine("sales")
        stage, cypher = engine.generate_cypher_batch_ingest(
            label="Order",
            id_field="order_id",
            properties=["order_id", "total_amount", "created_at"],
        )

        assert stage.passed is True
        assert "UNWIND $batch AS row" in cypher
        assert "MERGE (n:Order {order_id: row.order_id})" in cypher
        assert "row.total_amount" in cypher

    def test_recursive_sql_cte_query_generation(self, skill_dir: Path) -> None:
        """Assert generator creates cycle-safe recursive CTE queries."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from graph_pipeline_driver import KnowledgeGraphPipelineEngine

        engine = KnowledgeGraphPipelineEngine("org_chart")
        stage, sql = engine.generate_recursive_sql_traversal(
            table_name="employee_hierarchy",
            id_col="emp_id",
            parent_col="manager_id",
            max_depth=5,
        )

        assert stage.passed is True
        assert "WITH RECURSIVE graph_walk AS" in sql
        assert "ARRAY[emp_id] AS path" in sql
        assert "emp_id = ANY(gw.path)" in sql
        assert "NOT gw.is_cycle" in sql
        assert "gw.depth < 5" in sql
