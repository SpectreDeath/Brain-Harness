"""Contract verification tests for MemGraphRAG engine modular decomposition (Cycle 22)."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_submodule_direct_imports():
    """Verify all decomposed submodules can be imported independently without circular dependencies."""
    from plugins.memory_and_epistemics.memgraphrag.engine.models import (
        ConflictGroupModel,
        FactNode,
        PassageNode,
        SchemaNode,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.nlp import (
        _compute_tf_idf_vector,
        _cosine_similarity,
        _extract_triples_heuristic,
        _infer_entity_type,
        _tokenize,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.memory import ThreeLayerMemory
    from plugins.memory_and_epistemics.memgraphrag.engine.conflicts import (
        detect_conflicts_for_memory,
        resolve_conflicts_for_memory,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.graph import compile_memory_graph
    from plugins.memory_and_epistemics.memgraphrag.engine.retriever import retrieve_hybrid
    from plugins.memory_and_epistemics.memgraphrag.engine.synthesis import (
        calculate_memory_summary,
        synthesize_query_answer,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.core import MemGraphRAGEngine
    from plugins.memory_and_epistemics.memgraphrag.engine.resolvers import resolve_memgraphrag_engine

    assert SchemaNode is not None
    assert _tokenize is not None
    assert ThreeLayerMemory is not None
    assert detect_conflicts_for_memory is not None
    assert compile_memory_graph is not None
    assert retrieve_hybrid is not None
    assert synthesize_query_answer is not None
    assert MemGraphRAGEngine is not None
    assert resolve_memgraphrag_engine is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility():
    """Verify package __init__.py re-exports all legacy symbols."""
    from plugins.memory_and_epistemics.memgraphrag.engine import (
        ConflictGroupModel,
        FactNode,
        MemGraphRAGEngine,
        PassageNode,
        SchemaNode,
        ThreeLayerMemory,
        _compute_tf_idf_vector,
        _cosine_similarity,
        _tokenize,
    )

    assert MemGraphRAGEngine is not None
    assert ThreeLayerMemory is not None
    assert SchemaNode is not None
    assert FactNode is not None
    assert PassageNode is not None
    assert ConflictGroupModel is not None
    assert callable(_tokenize)
    assert callable(_compute_tf_idf_vector)
    assert callable(_cosine_similarity)


@pytest.mark.unit
def test_slotted_models_hygiene():
    """Verify dataclasses use slots=True per Rule 12."""
    from plugins.memory_and_epistemics.memgraphrag.engine.models import (
        FactNode,
        PassageNode,
        SchemaNode,
    )

    s = SchemaNode(idx=0, content=("Person", "founded", "Organization"))
    assert hasattr(s, "__slots__")

    f = FactNode(idx=0, content=("Ada", "founded", "Lab"))
    assert hasattr(f, "__slots__")

    p = PassageNode(idx=0, chunk_id="c1", content="Ada founded Lab.")
    assert hasattr(p, "__slots__")


@pytest.mark.unit
def test_nlp_heuristics_and_similarity():
    """Verify NLP tokenization, ontology inference, and TF-IDF similarity."""
    from plugins.memory_and_epistemics.memgraphrag.engine.nlp import (
        _compute_tf_idf_vector,
        _cosine_similarity,
        _extract_triples_heuristic,
        _infer_entity_type,
        _tokenize,
    )

    tokens = _tokenize("MemGraphRAG coordinates three layers of knowledge.")
    assert "graph" in tokens
    assert "rag" in tokens
    assert "knowledge" in tokens

    # Entity types
    assert _infer_entity_type("Dr. Lovelace") == "Person"
    assert _infer_entity_type("Cambridge University") == "Organization"
    assert _infer_entity_type("Neural Network Model") == "Technology"
    assert _infer_entity_type("95.5%") == "Quantity"

    # Triples heuristic
    triples = _extract_triples_heuristic("Graphiti was created by Zep AI. Harness manages agent plugins.")
    assert len(triples) >= 2

    # TF-IDF & Cosine similarity
    doc_freq = {"neural": 1, "network": 1, "quantum": 1}
    v1 = _compute_tf_idf_vector(["neural", "network"], doc_freq, 2)
    v2 = _compute_tf_idf_vector(["neural", "network"], doc_freq, 2)
    v3 = _compute_tf_idf_vector(["quantum"], doc_freq, 2)

    assert _cosine_similarity(v1, v2) > 0.99
    assert _cosine_similarity(v1, v3) == 0.0


@pytest.mark.unit
def test_three_layer_memory_operations():
    """Verify ThreeLayerMemory hierarchical linking and serialization."""
    from plugins.memory_and_epistemics.memgraphrag.engine.memory import ThreeLayerMemory

    mem = ThreeLayerMemory()
    p_idx = mem.get_or_create_passage("p100", "Alan Turing designed the Turing machine.")
    f_idx = mem.get_or_create_fact(("Alan Turing", "designed", "Turing Machine"))
    s_idx = mem.get_or_create_schema(("Person", "designed", "Technology"))

    mem.link_passage_and_fact(p_idx, f_idx)
    mem.link_fact_and_schema(f_idx, s_idx)

    assert mem.passage_layer[p_idx].fact_indices == [f_idx]
    assert mem.fact_layer[f_idx].schema_idx == s_idx
    assert mem.schema_layer[s_idx].fact_indices == [f_idx]

    d = mem.to_dict()
    restored = ThreeLayerMemory.from_dict(d)
    assert len(restored.passage_layer) == 1
    assert len(restored.fact_layer) == 1
    assert len(restored.schema_layer) == 1


@pytest.mark.unit
def test_conflict_detection_and_resolution():
    """Verify conflict group identification and evidence frequency resolution."""
    from plugins.memory_and_epistemics.memgraphrag.engine.conflicts import (
        detect_conflicts_for_memory,
        resolve_conflicts_for_memory,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.memory import ThreeLayerMemory

    mem = ThreeLayerMemory()
    p1 = mem.get_or_create_passage("p1", "Project X was founded in 2020.")
    p2 = mem.get_or_create_passage("p2", "Another source says Project X was founded in 2020.")
    p3 = mem.get_or_create_passage("p3", "Contradictory report says Project X was founded in 2024.")

    f1 = mem.get_or_create_fact(("Project X", "founded_in", "2020"))
    f2 = mem.get_or_create_fact(("Project X", "founded_in", "2024"))

    mem.link_passage_and_fact(p1, f1)
    mem.link_passage_and_fact(p2, f1)
    mem.link_passage_and_fact(p3, f2)

    conflicts = detect_conflicts_for_memory(mem)
    assert len(conflicts) == 1
    assert conflicts[0].head == "Project X"
    assert set(conflicts[0].conflicting_tails) == {"2020", "2024"}

    resolved_count = resolve_conflicts_for_memory(mem, conflicts)
    assert resolved_count == 1
    assert conflicts[0].resolved_tail == "2020"
    assert conflicts[0].resolution_status == "resolved"


@pytest.mark.unit
def test_graph_compilation_and_hybrid_retrieval():
    """Verify adjacency graph compilation and hybrid diffusion retrieval."""
    from plugins.memory_and_epistemics.memgraphrag.engine.graph import compile_memory_graph
    from plugins.memory_and_epistemics.memgraphrag.engine.memory import ThreeLayerMemory
    from plugins.memory_and_epistemics.memgraphrag.engine.retriever import retrieve_hybrid

    mem = ThreeLayerMemory()
    p = mem.get_or_create_passage("p1", "Claude is created by Anthropic.")
    f = mem.get_or_create_fact(("Claude", "created_by", "Anthropic"))
    s = mem.get_or_create_schema(("Technology", "created_by", "Organization"))
    mem.link_passage_and_fact(p, f)
    mem.link_fact_and_schema(f, s)

    graph_stats = compile_memory_graph(mem, "outputs/test")
    assert graph_stats["nodes_count"] >= 3
    assert graph_stats["edges_count"] >= 3

    ret = retrieve_hybrid(
        mem=mem,
        query="Who created Claude?",
        doc_frequencies={"claude": 1, "created": 1, "anthropic": 1},
        num_to_retrieve=2,
    )
    assert ret["status"] == "ok"
    assert len(ret["passages"]) == 1
    assert ret["passages"][0]["chunk_id"] == "p1"
    assert len(ret["facts"]) == 1


@pytest.mark.unit
def test_synthesis_and_summary_metrics():
    """Verify answer synthesis and summary stats."""
    from plugins.memory_and_epistemics.memgraphrag.engine.synthesis import (
        calculate_memory_summary,
        synthesize_query_answer,
    )
    from plugins.memory_and_epistemics.memgraphrag.engine.memory import ThreeLayerMemory

    mem = ThreeLayerMemory()
    p = mem.get_or_create_passage("p1", "Python 3.13 was released in October 2024.")
    f = mem.get_or_create_fact(("Python 3.13", "released_in", "October 2024"))
    s = mem.get_or_create_schema(("Technology", "released_in", "Quantity"))
    mem.link_passage_and_fact(p, f)
    mem.link_fact_and_schema(f, s)

    retrieval_payload = {
        "passages": [{"chunk_id": "p1", "content": "Python 3.13 was released in October 2024."}],
        "facts": [{"head": "Python 3.13", "relation": "released_in", "tail": "October 2024"}],
    }
    answer_res = synthesize_query_answer(query="When was Python 3.13 released?", retrieval_result=retrieval_payload)
    assert "Python 3.13" in answer_res["answer"]
    assert len(answer_res["reasoning_steps"]) >= 2

    stats = calculate_memory_summary(mem, graph_obj={"nodes_count": 3, "edges_count": 2}, save_dir="test_dir")
    assert stats["num_passages"] == 1
    assert stats["num_facts"] == 1
    assert stats["num_schemas"] == 1


@pytest.mark.unit
def test_single_seam_resolver():
    """Verify Rule 58 single-seam resolver resolve_memgraphrag_engine."""
    from plugins.memory_and_epistemics.memgraphrag.engine.resolvers import resolve_memgraphrag_engine
    from plugins.memory_and_epistemics.memgraphrag.engine.core import MemGraphRAGEngine

    # Without context
    engine1 = resolve_memgraphrag_engine()
    assert isinstance(engine1, MemGraphRAGEngine)

    # From context with provided service
    ctx = ServiceContext()
    engine2 = resolve_memgraphrag_engine(ctx)
    assert isinstance(engine2, MemGraphRAGEngine)


@pytest.mark.unit
def test_line_count_budgets():
    """Verify submodules stay under line count budgets."""
    subpackage = Path("plugins/memory_and_epistemics/memgraphrag/engine")
    for py_file in subpackage.glob("*.py"):
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 260, f"{py_file.name} exceeded 260 lines (was {len(lines)})"
