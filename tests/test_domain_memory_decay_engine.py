"""Tests for Domain: Memory Decay Engine plugin (Ebbinghaus Forgetting Model)."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.memory_and_epistemics.memory_decay_engine.decay_core import (
    EbbinghausMemoryEngine,
)
from plugins.memory_and_epistemics.memory_decay_engine.main import (
    MEMORY_DECAY_SERVICE_KEY,
    MemoryDecayService,
    export_memory_session,
    import_memory_session,
    memory_query_working_set,
    memory_recall,
    memory_register,
    memory_step,
    rank_working_set,
    simulate_session_benchmark,
)


@pytest.mark.unit
class TestMemoryDecayEnginePlugin:
    def test_ebbinghaus_decay_and_eviction(self) -> None:
        engine = EbbinghausMemoryEngine(eviction_threshold=0.20, base_stability=2.0)
        engine.register("ephemeral_fact", "This is an unreinforced fact.")
        assert len(engine.working_set()) == 1

        # Advance 6 turns: exp(-6/2) = exp(-3) = 0.049 < 0.20 -> evicted
        for _ in range(6):
            engine.step_turn()

        assert len(engine.working_set()) == 0
        assert engine.recall("ephemeral_fact") is None

    def test_channel_multipliers_and_foundational_protection(self) -> None:
        engine = EbbinghausMemoryEngine(eviction_threshold=0.20, base_stability=2.0)
        engine.register("inst", "System rules", channel="instruction")
        engine.register("tool", "Temp result", channel="tool_output")
        engine.register("found", "Core law", is_foundational=True)

        # Advance turns: tool_output should decay faster than instruction
        for _ in range(3):
            engine.step_turn()

        inst_item = engine.items["inst"]
        tool_item = engine.items["tool"]
        found_item = engine.items["found"]

        # Instruction has slower decay -> higher retention than tool_output
        assert inst_item.retention(engine.current_turn, decay_multiplier=0.25) > tool_item.retention(engine.current_turn, decay_multiplier=1.75)
        assert found_item.evicted is False

    def test_tool_workflow_and_session_export_import(self) -> None:
        sid = "test_sess_1"
        reg1 = memory_register("fact_a", "Alpha content", session_id=sid, stability=3.0)
        assert reg1["status"] == "ok"

        # Step 2 turns
        memory_step(session_id=sid)
        memory_step(session_id=sid)

        # Export session
        exp = export_memory_session(session_id=sid)
        assert exp["status"] == "ok"
        snapshot = exp["snapshot"]

        # Import into fresh session
        sid2 = "test_sess_restored"
        imp = import_memory_session(session_id=sid2, snapshot=snapshot)
        assert imp["status"] == "ok"
        assert imp["current_turn"] == 2
        assert imp["working_set_count"] == 1

        # Recall in restored session
        rec = memory_recall("fact_a", session_id=sid2)
        assert rec["status"] == "ok"
        assert rec["item"]["recall_count"] == 1

    def test_rank_working_set_tool(self) -> None:
        sid = "rank_sess"
        memory_register("fact_high", "Very important", session_id=sid, is_foundational=True)
        memory_register("fact_low", "Low importance", session_id=sid, is_foundational=False)

        ranked = rank_working_set(session_id=sid)
        assert ranked["status"] == "ok"
        assert len(ranked["items"]) == 2
        # Foundational item should be ranked first
        assert ranked["items"][0]["key"] == "fact_high"

    def test_simulation_benchmark_tool(self) -> None:
        res = simulate_session_benchmark(num_turns=30, total_memories=15, seed=42)
        assert res["status"] == "ok"
        sim = res["simulation"]
        assert "ebbinghaus_engine" in sim
        assert "recency_baseline" in sim
        assert sim["ebbinghaus_engine"]["foundational_lost"] == 0

    def test_service_facade_and_service_key(self) -> None:
        svc = MemoryDecayService()
        res = svc.register("k1", "content", session_id="svc_sess")
        assert res["status"] == "ok"
        assert MEMORY_DECAY_SERVICE_KEY.name == "domain.memory_decay_engine"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/memory_and_epistemics/memory_decay_engine")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0
