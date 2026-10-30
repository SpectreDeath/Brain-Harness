"""Unit and contract tests for Knowledge Graph derivation, models, and sync normalization.

Verifies AGENTS.md Rule 10 (CLI/API seams), Rule 12 (Slotted/Frozen dataclasses),
Rule 40 (Dual-file canonical directory format), Rule 43 (Frozen dataclass mutation invariant),
Rule 49 (Micro-kernel seam elevation), and Rule 58 (Single-seam IoC resolution).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.storage import (
    DerivedKnowledgeGraph,
    KNOWLEDGE_GRAPH_SERVICE_KEY,
    KnowledgeEdge,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphQueryService,
    KnowledgeGraphSummary,
    KnowledgeItemRecord,
    SQLiteStorageService,
    resolve_created_at,
    resolve_knowledge_graph_service,
    resolve_source_target,
    validate_export_path,
)


@pytest.mark.unit
class TestKnowledgeGraphModelsAndIoC:
    """Verifies slotted/frozen architecture and IoC container resolution."""

    def test_slotted_frozen_dataclass_invariants(self) -> None:
        """Rule 12 & Rule 43: Graph models must be slotted, frozen, and immutable."""
        node = KnowledgeGraphNode(
            id="ki_test_01",
            label="Test Node",
            node_kind="ki",
            category="memory_and_epistemics",
            domain="memory_and_epistemics",
            tags=("memory", "testing"),
            status="ACTIVE",
        )
        assert node.id == "ki_test_01"
        assert node.tags == ("memory", "testing")
        assert node.node_kind == "ki"

        # Rule 43: Direct attribute assignment must raise AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            node.status = "SUPERSEDED"  # type: ignore[misc]

        edge = KnowledgeGraphEdge(
            source="ki_test_01",
            target="ki_test_02",
            target_kind="ki",
            type="same_domain",
            derived=True,
            confidence=0.80,
            shared_tags=("memory",),
        )
        with pytest.raises((AttributeError, TypeError)):
            edge.confidence = 0.99  # type: ignore[misc]

        summary = KnowledgeGraphSummary(
            total_nodes=2,
            ki_nodes=2,
            non_ki_nodes_by_kind={},
            total_edges=1,
            edges_by_type={"same_domain": 1},
            derived_edge_count=1,
            asserted_edge_count=0,
            component_count=1,
            largest_component_size=2,
            isolated_ki_count=0,
            untagged_ki_count=0,
            uncategorized_ki_count=0,
            excluded_mega_tags=("mega_tag",),
        )
        graph = DerivedKnowledgeGraph(nodes=(node,), edges=(edge,), summary=summary)
        with pytest.raises((AttributeError, TypeError)):
            graph.summary = summary  # type: ignore[misc]

        # Serialization to dictionary
        d = graph.to_dict()
        assert d["summary"]["total_nodes"] == 2
        assert len(d["nodes"]) == 1
        assert len(d["edges"]) == 1
        assert d["nodes"][0]["id"] == "ki_test_01"

    def test_ioc_service_resolution_seam(self) -> None:
        """Rule 49 & Rule 58: Single-seam IoC resolution with fallback."""
        ctx = ServiceContext()
        custom_svc = KnowledgeGraphQueryService()
        ctx.provide(KNOWLEDGE_GRAPH_SERVICE_KEY, custom_svc)

        resolved = resolve_knowledge_graph_service(ctx)
        assert resolved is custom_svc

        # Fallback when context is empty
        empty_ctx = ServiceContext()
        fallback = resolve_knowledge_graph_service(empty_ctx)
        assert isinstance(fallback, KnowledgeGraphQueryService)
        assert fallback is not custom_svc

        # None context fallback
        none_fallback = resolve_knowledge_graph_service(None)
        assert isinstance(none_fallback, KnowledgeGraphQueryService)

    def test_export_path_guardrails(self, tmp_path: Path) -> None:
        """Rule 40: Exports must reject target paths inside .harness/knowledge."""
        vault_dir = tmp_path / ".harness" / "knowledge"
        vault_dir.mkdir(parents=True)

        # External output path must succeed
        valid_out = tmp_path / "exports" / "graph.gexf"
        validated = validate_export_path(valid_out, vault_dir=vault_dir)
        assert validated == valid_out.resolve()

        # Path inside vault must fail
        invalid_out = vault_dir / "graph.gexf"
        with pytest.raises(ValueError, match="forbidden by Rule 40"):
            validate_export_path(invalid_out, vault_dir=vault_dir)


@pytest.mark.unit
class TestKnowledgeVaultSyncNormalization:
    """Verifies lossless normalization of heterogeneous on-disk formats."""

    @pytest.mark.asyncio
    async def test_heterogeneous_metadata_normalization(self, tmp_path: Path) -> None:
        """Verify normalization of string isnad, top-level claims, ki_id, and creation waterfall."""
        vault_dir = tmp_path / ".harness" / "knowledge"
        vault_dir.mkdir(parents=True)

        # Item 1: Plain string isnad and source_repo
        ki1_dir = vault_dir / "ki_audit_20260908_01"
        ki1_dir.mkdir()
        (ki1_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_audit_20260908_01",
            "title": "Clock Sensitive Smell",
            "source_repo": "https://github.com/example/repo",
            "isnad": "Audited via deep-repo-auditor",
            "tags": ["testing", "clock-sensitive"],
            "category": "testing_and_verification",
            "created_at": "2026-09-08T19:45:00Z",
        }), encoding="utf-8")
        (ki1_dir / "summary.md").write_text("Avoid time-dependent assertions.", encoding="utf-8")

        # Item 2: Top-level claims array and ki_id alias
        ki2_dir = vault_dir / "ki_bridge_feature"
        ki2_dir.mkdir()
        (ki2_dir / "metadata.json").write_text(json.dumps({
            "ki_id": "ki_bridge_feature",
            "title": "Bridge Feature Definition",
            "source": {"url": "https://github.com/example/bridge", "git_commit": "abc1234"},
            "claims": [{"assertion": "Bridges must decouple transports", "verified": True}],
            "tags": ["bridge", "transport"],
            "category": "software_engineering",
            "timestamp": "2026-09-10T12:00:00Z",
        }), encoding="utf-8")
        (ki2_dir / "summary.md").write_text("Decouple transports from adapters.", encoding="utf-8")

        # Item 3: Regex date in folder name and unmapped category
        ki3_dir = vault_dir / "ki_20260912_sandboxing"
        ki3_dir.mkdir()
        (ki3_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_20260912_sandboxing",
            "title": "Subprocess Sandboxing Invariant",
            "source_target": "src/harness/sandbox/factory.py",
            "tags": ["sandbox", "isolation"],
            "category": "security_and_sandboxing",
        }), encoding="utf-8")
        (ki3_dir / "summary.md").write_text("Default to subprocess isolation.", encoding="utf-8")

        storage = SQLiteStorageService(":memory:")
        synced = await storage.sync_knowledge_vault(vault_dir)
        assert synced == 3

        items = await storage.list_knowledge_items()
        assert len(items) == 3
        id_map = {k.id: k for k in items}

        # Assert Item 1 normalization
        item1 = id_map["ki_audit_20260908_01"]
        assert isinstance(item1.isnad, dict)
        assert item1.isnad["status"] == "VERIFIED"
        assert item1.isnad["notes"] == "Audited via deep-repo-auditor"
        assert item1.source_target == "https://github.com/example/repo"
        assert item1.category == "developer_experience/testing"
        assert item1.created_at == "2026-09-08T19:45:00Z"

        # Assert Item 2 normalization
        item2 = id_map["ki_bridge_feature"]
        assert item2.id == "ki_bridge_feature"
        assert item2.source_target == "https://github.com/example/bridge"
        assert item2.category == "developer_experience/software_engineering"
        claims = item2.get_claims()
        assert len(claims) == 1
        assert "Bridges must decouple transports" in claims[0].assertion

        # Assert Item 3 normalization
        item3 = id_map["ki_20260912_sandboxing"]
        assert item3.category == "security_and_forensics/sandboxing"
        assert item3.created_at == "2026-09-12T00:00:00Z"
        assert item3.source_target == "src/harness/sandbox/factory.py"
        # Verify mechanical backfill attached code reference
        assert any(e.type == "references_code" and e.target == "src/harness/sandbox/factory.py" for e in item3.edges)

        storage.close()


@pytest.mark.unit
class TestKnowledgeGraphDerivationEngine:
    """Verifies graph edge derivation, mega-tag frequency capping, and node materialization."""

    def test_mega_tag_filtering_and_edge_derivation(self) -> None:
        """Verify mega-tag cap (>15%), same_domain threshold, and heterogeneous materialization."""
        # Create 20 items: "common_tag" on 16 items (80% > 15%), "spec_tag" on 2 items (10% <= 15%) in same domain
        items: list[KnowledgeItemRecord] = []
        for i in range(1, 21):
            tags = ["common_tag"] if i <= 16 else []
            cat = "developer_experience/architecture" if i <= 10 else "data_engineering/storage"
            if i in (1, 2):
                tags.extend(["spec_tag", "secondary_spec"])
            items.append(KnowledgeItemRecord(
                id=f"ki_{i:02d}",
                title=f"Pattern {i}",
                category=cat,
                tags=tags,
                source_target="src/harness/core.py" if i == 1 else "",
            ))

        # Add explicit non-KI edge to item 1
        items[0].add_edge("became_skill", "agent-architect", target_kind="skill", confidence=1.0)

        svc = KnowledgeGraphQueryService()
        graph = svc.derive_graph(items, nodes_filter="all", max_tag_freq=0.15)

        # Summary assertions
        assert "common_tag" in graph.summary.excluded_mega_tags
        assert "spec_tag" not in graph.summary.excluded_mega_tags
        assert graph.summary.ki_nodes == 20
        # 20 KIs + 1 materialized skill node = 21 total nodes
        assert graph.summary.total_nodes == 21
        assert graph.summary.non_ki_nodes_by_kind.get("skill") == 1

        # Edge assertions:
        # 1 asserted edge (became_skill) + 1 derived edge (between ki_01 and ki_02 on spec_tag + secondary_spec)
        assert graph.summary.asserted_edge_count == 1
        assert graph.summary.derived_edge_count == 1
        assert graph.summary.total_edges == 2

        # Check materialized skill node
        node_map = {n.id: n for n in graph.nodes}
        assert "agent-architect" in node_map
        skill_node = node_map["agent-architect"]
        assert skill_node.node_kind == "skill"
        assert skill_node.status == "EXTERNAL"

        # Check ki-only filter
        ki_graph = svc.derive_graph(items, nodes_filter="ki-only", max_tag_freq=0.15)
        assert ki_graph.summary.total_nodes == 20
        assert ki_graph.summary.total_edges == 1
        assert ki_graph.edges[0].type == "same_domain"

    def test_live_vault_sync_and_derivation_integrity(self) -> None:
        """Verify that all 282 on-disk vault items sync cleanly without dropping any items."""
        vault_path = Path(".harness/knowledge")
        if not vault_path.exists():
            pytest.skip("Live .harness/knowledge directory not found")

        dirs = [d for d in vault_path.iterdir() if d.is_dir() and (d / "metadata.json").exists()]
        expected_count = len(dirs)
        assert expected_count >= 282

        svc = KnowledgeGraphQueryService()
        # Test direct resolution functions across all live metadata files
        parsed_items = []
        for d in dirs:
            meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
            ki_id = meta.get("id") or meta.get("ki_id") or d.name
            st = resolve_source_target(meta)
            ca = resolve_created_at(meta, d)
            edges = [KnowledgeEdge.model_validate(e) for e in meta.get("edges", [])]
            ki = KnowledgeItemRecord(
                id=ki_id,
                title=meta.get("title", ki_id),
                source_target=st,
                tags=meta.get("tags", []),
                category=meta.get("category") or "general",
                edges=edges,
                created_at=ca,
            )
            parsed_items.append(ki)

        assert len(parsed_items) == expected_count

        graph = svc.derive_graph(parsed_items, max_tag_freq=0.15)
        assert graph.summary.ki_nodes == expected_count
        assert "endogenous_memory" in graph.summary.excluded_mega_tags
        assert "self_reflection" in graph.summary.excluded_mega_tags
        assert graph.summary.total_nodes >= expected_count
        assert graph.summary.total_edges >= 7
