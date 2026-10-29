"""Contract verification test suite for Headroom Context Optimizer service, plugin, and tools."""

import json
import pytest
from unittest.mock import MagicMock

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.headroom_optimizer import (
    HEADROOM_CONTEXT_OPTIMIZER_KEY,
    CacheDriftResult,
    ContentCompressResult,
    DedupTurnsResult,
    HeadroomContextOptimizerService,
    SavingsLedger,
    ThinkingCompactResult,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry
from plugins.memory_and_epistemics.headroom_context_optimizer.main import (
    HeadroomContextOptimizerEngine,
    HeadroomContextOptimizerPlugin,
    plugin,
)


class TestHeadroomContextOptimizerContracts:
    """Verifies architectural contracts, slotted models, transforms, and tool mounting."""

    def test_service_key_and_protocol_conformance(self) -> None:
        """Verify service key naming and protocol runtime compliance."""
        assert isinstance(HEADROOM_CONTEXT_OPTIMIZER_KEY, ServiceKey)
        assert HEADROOM_CONTEXT_OPTIMIZER_KEY.name == "memory.headroom_context_optimizer"

        engine = HeadroomContextOptimizerEngine()
        assert isinstance(engine, HeadroomContextOptimizerService)

    def test_slotted_frozen_dataclass_immutability_and_validation(self) -> None:
        """Verify Rule 12 and Rule 43: slotted frozen dataclasses cannot be mutated."""
        result = ContentCompressResult(
            status="ok",
            original_tokens=100,
            compressed_tokens=40,
            savings_ratio=0.6,
            strategy="smart_crusher_json",
            compressed_text="{}",
        )

        # Rule 43: Direct attribute assignment inside pytest.raises
        with pytest.raises((AttributeError, TypeError)):
            result.status = "error"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            result.compressed_tokens = 0  # type: ignore[misc]

        # Post-init validation tests
        with pytest.raises(ValueError, match="Invalid status"):
            ContentCompressResult(
                status="invalid_status",
                original_tokens=10,
                compressed_tokens=5,
                savings_ratio=0.5,
                strategy="test",
                compressed_text="",
            )

        with pytest.raises(ValueError, match="savings_ratio must be between 0.0 and 1.0"):
            ContentCompressResult(
                status="ok",
                original_tokens=10,
                compressed_tokens=5,
                savings_ratio=1.5,
                strategy="test",
                compressed_text="",
            )

    def test_content_router_json_array_smart_crushing(self) -> None:
        """Verify SmartCrusher JSON array compaction on large records."""
        engine = HeadroomContextOptimizerEngine()
        data = [{"id": i, "name": f"item_{i}", "val": i * 10} for i in range(20)]
        raw_json = json.dumps(data)

        res = engine.compress_content(raw_json, content_type="json")
        assert res.status == "ok"
        assert res.strategy == "smart_crusher_json"
        assert res.compressed_tokens < res.original_tokens
        assert res.savings_ratio > 0.0

        parsed = json.loads(res.compressed_text)
        assert parsed["_headroom_smart_crush"] is True
        assert parsed["total_rows"] == 20
        assert "schema_keys" in parsed
        assert len(parsed["head_sample"]) == 3
        assert len(parsed["tail_sample"]) == 2

    def test_content_router_code_and_log_transforms(self) -> None:
        """Verify code whitespace compaction and log middle-truncation."""
        engine = HeadroomContextOptimizerEngine()

        # Code compaction
        code_input = "def hello():\n\n\n    print('hi')\n\n\n    return 42\n"
        res_code = engine.compress_content(code_input, content_type="code")
        assert res_code.status == "ok"
        assert res_code.strategy == "code_whitespace_collapsed"
        assert "\n\n\n" not in res_code.compressed_text

        # Log middle-truncation
        log_input = "\n".join([f"2026-10-28 10:00:{i:02d} INFO Step execution line {i}" for i in range(50)])
        res_log = engine.compress_content(log_input, content_type="log")
        assert res_log.status == "ok"
        assert res_log.strategy == "log_truncated"
        assert "lines omitted" in res_log.compressed_text
        assert len(res_log.compressed_text.splitlines()) == 21

    def test_cross_turn_dedup_ccr_markers(self) -> None:
        """Verify Cross-Context Retrieval (CCR) deduplication replaces repeated tool observations."""
        engine = HeadroomContextOptimizerEngine()

        large_tool_output = "\n".join([f"file_record_{i}.py - 1024 bytes - modified recently" for i in range(10)])
        messages = [
            {"role": "user", "content": "list directory contents"},
            {"role": "assistant", "content": large_tool_output},
            {"role": "user", "content": "run another check and list again"},
            {"role": "assistant", "content": large_tool_output},  # Identical repeat
            {"role": "user", "content": "now test single small line"},
            {"role": "assistant", "content": "ok, done."},  # Small, should NOT fold
        ]

        res = engine.dedup_turns(messages, min_lines=3, min_chars=40)
        assert res.status == "ok"
        assert res.deduplicated_blocks == 1
        assert res.tokens_saved > 0

        # First assistant message remains untouched
        assert res.compacted_messages[1]["content"] == large_tool_output
        # Second identical assistant message is replaced with CCR digest marker
        assert "[CCR tool digest:" in res.compacted_messages[3]["content"]
        # Small assistant message is untouched
        assert res.compacted_messages[5]["content"] == "ok, done."

    def test_cache_alignment_drift_detection(self) -> None:
        """Verify structural parsing of volatile tokens without mutating system prompt."""
        engine = HeadroomContextOptimizerEngine()

        # Stable system prompt
        stable_prompt = "You are an autonomous engineering agent designed to follow repository rules."
        res_stable = engine.detect_cache_drift(stable_prompt)
        assert res_stable.status == "ok"
        assert res_stable.is_cache_stable is True
        assert len(res_stable.volatile_items) == 0

        # Volatile system prompt containing UUID, timestamp, and hash
        volatile_prompt = (
            "Session: 12345678-1234-5678-1234-567812345678\n"
            "Timestamp: 2026-10-28T18:45:00Z\n"
            "Commit: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0\n"
            "Execute task with maximum rigor."
        )
        res_volatile = engine.detect_cache_drift(volatile_prompt)
        assert res_volatile.status == "ok"
        assert res_volatile.is_cache_stable is False
        assert len(res_volatile.volatile_items) == 3
        types = {item["type"] for item in res_volatile.volatile_items}
        assert "uuid" in types
        assert "timestamp_iso8601" in types
        assert "hex_hash" in types
        assert len(res_volatile.recommendations) > 0

    def test_thinking_compaction(self) -> None:
        """Verify prior-turn thinking block compaction with recent window preservation."""
        engine = HeadroomContextOptimizerEngine()

        messages = [
            {"role": "user", "content": "Task 1"},
            {"role": "assistant", "content": "<thinking>\nDeep architectural reasoning step 1\nAnalyzing context\n</thinking>\nResult 1"},
            {"role": "user", "content": "Task 2"},
            {"role": "assistant", "content": "<thinking>\nDeep architectural reasoning step 2\nRefining models\n</thinking>\nResult 2"},
            {"role": "user", "content": "Task 3"},
            {"role": "assistant", "content": "<thinking>\nActive reasoning step 3\nFinalizing answer\n</thinking>\nResult 3"},
        ]

        # Preserve the last 1 assistant turn
        res = engine.compact_thinking(messages, keep_last_turns=1)
        assert res.status == "ok"
        assert res.compacted_turns == 2
        assert res.tokens_saved > 0

        # Turn 1 and 2 thinking compacted
        assert "[prior reasoning, compressed:" in res.messages[1]["content"]
        assert "<thinking>" not in res.messages[1]["content"]
        assert "[prior reasoning, compressed:" in res.messages[3]["content"]

        # Last assistant turn keeps active thinking intact
        assert "<thinking>" in res.messages[5]["content"]
        assert "Active reasoning step 3" in res.messages[5]["content"]

    def test_savings_ledger_tracking_and_reset(self) -> None:
        """Verify cumulative token and dollar savings ledger."""
        engine = HeadroomContextOptimizerEngine()
        engine.compress_content("[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", content_type="json")

        ledger = engine.get_savings_metrics(reset=False)
        assert isinstance(ledger, SavingsLedger)
        assert ledger.total_in_tokens > 0

        # Reset ledger
        ledger_reset = engine.get_savings_metrics(reset=True)
        ledger_empty = engine.get_savings_metrics(reset=False)
        assert ledger_empty.total_in_tokens == 0
        assert ledger_empty.net_tokens_saved == 0

    @pytest.mark.asyncio
    async def test_plugin_lifecycle_and_tool_registration(self) -> None:
        """Verify plugin loads, provides service into IoC, and registers tools."""
        ctx = ServiceContext()
        tool_reg = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, tool_reg)

        test_plugin = HeadroomContextOptimizerPlugin()
        assert test_plugin.name == "plugin.headroom_context_optimizer"
        assert HEADROOM_CONTEXT_OPTIMIZER_KEY in test_plugin.provides
        assert TOOL_REGISTRY_KEY in test_plugin.requires

        await test_plugin.on_load(ctx)
        assert ctx.has(HEADROOM_CONTEXT_OPTIMIZER_KEY)

        await test_plugin.on_enable()

        # Verify all 5 tools are mounted
        expected_tools = [
            "headroom_compress_content",
            "headroom_dedup_turns",
            "headroom_detect_cache_drift",
            "headroom_compact_thinking",
            "headroom_savings_metrics",
        ]
        for tool_name in expected_tools:
            assert tool_reg.get(tool_name) is not None
            assert tool_reg.is_tool_enabled(tool_name)

        # Test tool invocation via registry
        compress_tool = tool_reg.get("headroom_compress_content")
        assert compress_tool is not None
        out = compress_tool.executor(content="hello world text content", content_type="text")
        assert isinstance(out, dict)
        assert out["status"] == "ok"
        assert "compressed_tokens" in out
