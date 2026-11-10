"""Unit tests for MemGraphRAG service definition and IoC container resolution."""

import pytest
from harness.kernel.context import ServiceContext
from harness.services.memgraphrag import (
    MEMGRAPHRAG_MEMORY_KEY,
    MemGraphRAGIndexResult,
    MemGraphRAGQueryResult,
    MemGraphRAGRetrieveResult,
    MemGraphRAGService,
    MemGraphRAGSummaryResult,
    PassageResult,
)
from plugins.memory_and_epistemics.memgraphrag.main import MemGraphRAGPlugin


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memgraphrag_service_key_resolution():
    ctx = ServiceContext()
    plugin = MemGraphRAGPlugin()
    
    await plugin.on_load(ctx)
    
    assert ctx.has(MEMGRAPHRAG_MEMORY_KEY)
    service = ctx.require(MEMGRAPHRAG_MEMORY_KEY)
    assert isinstance(service, MemGraphRAGService)

    # Test basic retrieval through service
    res = await service.index(
        docs=["Three-layer memory bridges schemas, facts, and passages."],
        save_dir="outputs/test_service",
    )
    assert isinstance(res, MemGraphRAGIndexResult)
    assert res.status == "ok"

    ret = await service.retrieve(query="Three-layer memory", save_dir="outputs/test_service")
    assert isinstance(ret, MemGraphRAGRetrieveResult)
    assert len(ret.passages) >= 1

    ans = await service.query(query="What is three-layer memory?", save_dir="outputs/test_service")
    assert isinstance(ans, MemGraphRAGQueryResult)
    assert len(ans.retrieved_passages) >= 1

    added = await service.add_passage(
        chunk_id="custom_p2",
        content="KWS Streaming runs keyword spotting on microcontrollers.",
        extracted_triples=[["KWS Streaming", "runs_on", "microcontrollers"]],
        save_dir="outputs/test_service",
    )
    assert isinstance(added, PassageResult)

    summary = await service.get_summary(save_dir="outputs/test_service")
    assert isinstance(summary, MemGraphRAGSummaryResult)
    assert summary.num_passages >= 2
