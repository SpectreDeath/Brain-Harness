"""Tests for MemGraphRAG 3-Layer Memory Plugin and Engine."""

import pytest
import shutil
from pathlib import Path

from harness.kernel.context import ServiceContext
from harness.services.memgraphrag import MEMGRAPHRAG_MEMORY_KEY

from plugins.memory_and_epistemics.memgraphrag.engine import (
    MemGraphRAGEngine,
    ThreeLayerMemory,
)
from plugins.memory_and_epistemics.memgraphrag.main import (
    MemGraphRAGPlugin,
    memgraphrag_add_passage,
    memgraphrag_detect_conflicts,
    memgraphrag_get_memory_summary,
    memgraphrag_index,
    memgraphrag_query,
    memgraphrag_retrieve,
)
from plugins.memory_and_epistemics.memgraphrag.models import (
    FactNode,
    PassageNode,
    SchemaNode,
)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> str:
    save_dir = str(tmp_path / "memgraph_test")
    yield save_dir
    if Path(save_dir).exists():
        shutil.rmtree(save_dir, ignore_errors=True)


@pytest.mark.unit
def test_three_layer_memory_basic_operations():
    mem = ThreeLayerMemory()
    
    # 1. Create passage
    p_idx = mem.get_or_create_passage("p1", "Ada Lovelace developed the first algorithm for the Analytical Engine.")
    assert p_idx == 0
    assert len(mem.passage_layer) == 1

    # 2. Create fact
    f_idx = mem.get_or_create_fact(("Ada Lovelace", "developed", "Analytical Engine"))
    assert f_idx == 0
    assert len(mem.fact_layer) == 1

    # 3. Create schema
    s_idx = mem.get_or_create_schema(("Person", "developed", "Technology"))
    assert s_idx == 0
    assert len(mem.schema_layer) == 1

    # 4. Link hierarchy
    mem.link_passage_and_fact(p_idx, f_idx)
    mem.link_fact_and_schema(f_idx, s_idx)

    assert f_idx in mem.passage_layer[p_idx].fact_indices
    assert p_idx in mem.fact_layer[f_idx].passage_indices
    assert mem.fact_layer[f_idx].schema_idx == s_idx
    assert f_idx in mem.schema_layer[s_idx].fact_indices
    assert mem.fact_layer[f_idx].frequency == 1
    assert mem.schema_layer[s_idx].frequency == 1

    # 5. Serialization roundtrip
    d = mem.to_dict()
    mem_restored = ThreeLayerMemory.from_dict(d)
    assert len(mem_restored.passage_layer) == 1
    assert len(mem_restored.fact_layer) == 1
    assert len(mem_restored.schema_layer) == 1
    assert mem_restored.fact_layer[0].content == ("Ada Lovelace", "developed", "Analytical Engine")


@pytest.mark.unit
def test_memgraphrag_index_and_conflict_resolution(temp_output_dir: str):
    docs = [
        {
            "idx": "chunk_1",
            "content": "Graphiti was created by Zep AI in 2024.",
            "triples": [["Graphiti", "created_by", "Zep AI"]],
        },
        {
            "idx": "chunk_2",
            "content": "Graphiti was created by OpenAI.",
            "triples": [["Graphiti", "created_by", "OpenAI"]],
        },
        {
            "idx": "chunk_3",
            "content": "Graphiti uses bi-temporal edge invalidation.",
            "triples": [["Graphiti", "uses", "bi-temporal edge invalidation"]],
        },
        {
            "idx": "chunk_4",
            "content": "Another report affirms Graphiti was created by Zep AI for temporal memory.",
            "triples": [["Graphiti", "created_by", "Zep AI"]],
        },
    ]

    index_res = memgraphrag_index(
        docs=docs,
        save_dir=temp_output_dir,
        skip_conflict_resolution=False,
    )

    assert index_res["status"] == "ok"
    assert index_res["passages_count"] == 4
    assert index_res["conflicts_detected"] >= 1
    assert index_res["conflicts_resolved"] >= 1
    assert index_res["graph_nodes_count"] > 0
    assert index_res["graph_edges_count"] > 0

    # Inspect conflicts tool
    conflicts_res = memgraphrag_detect_conflicts(save_dir=temp_output_dir)
    assert conflicts_res["status"] == "ok"
    assert len(conflicts_res["conflicts"]) >= 1
    conflict = conflicts_res["conflicts"][0]
    assert conflict["head"] == "Graphiti"
    assert conflict["relation"] == "created_by"
    assert conflict["resolved_tail"] == "Zep AI"


@pytest.mark.unit
def test_memgraphrag_retrieve_and_query(temp_output_dir: str):
    docs = [
        "MemGraphRAG organizes knowledge into three connected layers: schema, fact, and passage.",
        "The schema layer abstracts concrete facts into reusable ontology triples.",
        "Conflict groups are resolved using supporting passage evidence.",
    ]

    memgraphrag_index(docs=docs, save_dir=temp_output_dir)

    # Test retrieval
    ret = memgraphrag_retrieve(
        query="three connected layers in MemGraphRAG",
        save_dir=temp_output_dir,
        num_to_retrieve=2,
    )

    assert ret["status"] == "ok"
    assert len(ret["passages"]) > 0
    assert ret["retrieved_count"] > 0
    assert any("three connected layers" in p["content"] for p in ret["passages"])

    # Test QA query
    q_res = memgraphrag_query(
        query="What does the schema layer do?",
        save_dir=temp_output_dir,
        num_passages=2,
    )
    assert q_res["status"] == "ok"
    assert "schema layer" in q_res["answer"].lower()
    assert len(q_res["retrieved_passages"]) > 0


@pytest.mark.unit
def test_memgraphrag_incremental_add_passage(temp_output_dir: str):
    # Initialize empty
    summary_init = memgraphrag_get_memory_summary(save_dir=temp_output_dir)
    assert summary_init["num_passages"] == 0

    # Incrementally add passage
    p_res = memgraphrag_add_passage(
        chunk_id="chunk_inc_1",
        content="Antigravity provides advanced agentic pair-programming workflows.",
        extracted_triples=[["Antigravity", "provides", "agentic workflows"]],
        schema_tuple=["Technology", "provides", "Concept"],
        save_dir=temp_output_dir,
    )

    assert p_res["chunk_id"] == "chunk_inc_1"
    assert len(p_res["fact_indices"]) == 1

    summary_after = memgraphrag_get_memory_summary(save_dir=temp_output_dir)
    assert summary_after["num_passages"] == 1
    assert summary_after["num_facts"] == 1
    assert summary_after["num_schemas"] == 1


@pytest.mark.asyncio
async def test_memgraphrag_plugin_service_lifecycle(temp_output_dir: str):
    plugin = MemGraphRAGPlugin()
    ctx = ServiceContext()

    # Verify lifecycle hooks
    await plugin.on_load(ctx)
    await plugin.on_enable()

    # Verify IoC service registration & resolution
    service = ctx.require(MEMGRAPHRAG_MEMORY_KEY)
    assert service is not None

    # Test service index method
    idx_res = await service.index(
        docs=["Harness microkernel coordinates plugins with typed IoC service keys."],
        save_dir=temp_output_dir,
    )
    assert idx_res.status == "ok"
    assert idx_res.passages_count == 1

    # Test service retrieve method
    ret_res = await service.retrieve(
        query="Harness microkernel",
        num_to_retrieve=1,
    )
    assert ret_res.status == "ok"

    # Test service get_summary
    summ_res = await service.get_summary(save_dir=temp_output_dir)
    assert summ_res.num_passages == 1

    await plugin.on_disable()
    await plugin.on_unload()
