"""Tests for AgentWikis IoC Service, Plugin lifecycle, and Deepened Engine seams."""

from __future__ import annotations

import asyncio
from pathlib import Path
import time
import pytest

from harness.kernel.context import ServiceContext
from harness.services.agentwikis import AGENTWIKIS_SERVICE_KEY, AgentWikisService
from plugins.integration_and_io.agentwikis.main import AgentWikisPlugin, plugin as agentwikis_plugin_singleton
from agentwikis_engine import (
    AgentWikisEngine,
    DocumentBlockOffset,
    DocumentOffsetTable,
    DocumentSlice,
    MatchResult,
    SearchHit,
    WikiEntity,
    WikiScope,
)


@pytest.mark.unit
class TestAgentWikisIoCService:
    """Verify Harness Rule 1 & Rule 2: IoC container registration and protocol conformity."""

    def test_protocol_conformity(self) -> None:
        """Verify AgentWikisEngine and AgentWikisPlugin satisfy AgentWikisService protocol."""
        assert isinstance(agentwikis_plugin_singleton, AgentWikisService)
        engine = AgentWikisEngine()
        assert isinstance(engine, AgentWikisService)

    @pytest.mark.asyncio
    async def test_plugin_registration_and_ioc_resolution(self) -> None:
        """Verify plugin registers AGENTWIKIS_SERVICE_KEY into ServiceContext."""
        ctx = ServiceContext()
        plugin = AgentWikisPlugin()

        assert AGENTWIKIS_SERVICE_KEY in plugin.provides
        assert plugin.requires == []
        assert plugin.name == "plugin.agentwikis"

        await plugin.on_load(ctx)

        resolved = ctx.require(AGENTWIKIS_SERVICE_KEY)
        assert resolved is not None
        assert isinstance(resolved, AgentWikisService)

        # Test listing wikis via resolved service
        wikis = resolved.list_wikis(category="inference")
        assert len(wikis) > 0
        slugs = [w.slug for w in wikis]
        assert "vllm" in slugs or "llama-cpp" in slugs

        # Test scope inspection via resolved service
        scope = resolved.get_scope("hermes")
        assert scope is not None
        assert "Hermes Agent" in scope.covers


@pytest.mark.unit
class TestDeepenedEngineSeams:
    """Verify O(1) byte-offset indexing, in-engine search, and context packing."""

    def test_byte_offset_indexing_and_seeking(self) -> None:
        """Verify lazy byte-offset table builds and enables sub-millisecond seek extraction."""
        engine = AgentWikisEngine()
        offset_table = engine._ensure_offset_table()

        if offset_table is not None:
            assert offset_table.total_blocks >= 1000
            assert "hermes/wiki/concepts/bot-mode.md" in offset_table.offsets

            # Measure seek extraction speed
            t0 = time.perf_counter()
            slice_doc = engine.extract_document("hermes/wiki/concepts/bot-mode.md")
            t_elapsed_ms = (time.perf_counter() - t0) * 1000

            assert slice_doc is not None
            assert slice_doc.wiki_slug == "hermes"
            assert "Bot Mode" in slice_doc.content
            assert slice_doc.source_isnad == "local_llms_full_txt"
            # O(1) seek should execute in well under 50ms
            assert t_elapsed_ms < 50.0

    def test_in_engine_search_and_confidence(self) -> None:
        """Verify search logic encapsulated in engine returns calibrated SearchHit objects."""
        engine = AgentWikisEngine()
        hits = engine.search(query="bot mode", wiki="hermes", limit=3)

        assert len(hits) > 0
        assert len(hits) <= 3
        top = hits[0]
        assert isinstance(top, SearchHit)
        assert top.calibrated_confident is True
        assert top.score >= 5.0
        assert "hermes" in top.wiki_slug

    def test_batch_extract_slices(self) -> None:
        """Verify multi-document batch extraction in a single operation."""
        engine = AgentWikisEngine()
        specs = [
            ("hermes/README.md", None),
            ("hermes/wiki/concepts/bot-mode.md", "Bot Mode & Teammate Rooms"),
        ]
        slices = engine.batch_extract(specs)
        assert len(slices) == 2
        assert slices[0].wiki_slug == "hermes"
        assert len(slices[0].content) > 10
        assert slices[1].section == "Bot Mode & Teammate Rooms"

    def test_prepare_context_pack_in_scope(self) -> None:
        """Verify prepare_context_pack bounds tokens and formats Isnad provenance."""
        engine = AgentWikisEngine()
        pack = engine.prepare_context_pack("fine-tuning models with unsloth", max_tokens=1000)

        assert "# AgentWikis Context Pack" in pack
        assert "unsloth" in pack.lower()
        assert "## Provenance & Isnad Lineage" in pack
        # Assert token bound (1000 tokens ≈ max 4000-5000 chars)
        assert len(pack) <= 5500

    def test_prepare_context_pack_out_of_scope(self) -> None:
        """Verify prepare_context_pack gracefully rejects out-of-scope prompts."""
        engine = AgentWikisEngine()
        pack = engine.prepare_context_pack("how to bake sourdough bread in high altitude")

        assert "Out of Scope" in pack
        assert "sourdough bread" in pack


@pytest.mark.unit
def test_offset_dataclasses_immutability() -> None:
    """Verify Rule 12 and Rule 43: Slotted & Frozen Dataclass Immutability for new models."""
    block = DocumentBlockOffset(
        wiki_slug="vllm",
        relative_path="README.md",
        byte_offset=1024,
        byte_length=512,
    )
    assert block.byte_offset == 1024

    with pytest.raises((AttributeError, TypeError)):
        block.byte_offset = 2048  # type: ignore

    table = DocumentOffsetTable(
        corpus_file="llms-full.txt",
        total_blocks=1,
        offsets={"vllm/README.md": (1024, 512)},
    )
    assert table.total_blocks == 1

    with pytest.raises((AttributeError, TypeError)):
        table.total_blocks = 5  # type: ignore
