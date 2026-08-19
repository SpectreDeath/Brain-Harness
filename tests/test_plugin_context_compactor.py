"""Tests for context_compactor plugin."""

from __future__ import annotations

import pytest

from plugins.memory_and_epistemics.context_compactor.main import (
    compact_conversation,
    offload_to_memory,
    recall_context,
)


@pytest.mark.unit
class TestContextCompactorPlugin:
    def test_compact_conversation_small(self) -> None:
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        res = compact_conversation(messages, preserve_recent=4)
        assert res["status"] == "ok"
        assert res["summarized"] is False
        assert len(res["compacted_messages"]) == 2

    def test_compact_conversation_large(self) -> None:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for i in range(10):
            messages.append({"role": "user", "content": f"User question {i}"})
            messages.append({"role": "assistant", "content": f"Assistant answer {i}"})

        res = compact_conversation(messages, preserve_recent=4)
        assert res["status"] == "ok"
        assert res["summarized"] is True
        assert res["compacted_count"] < res["original_count"]
        # System prompt preserved + condensed summary injected + 4 recent turns
        assert res["compacted_messages"][0]["role"] == "system"
        assert "[CONTEXT SUMMARY" in res["compacted_messages"][1]["content"]

    def test_offload_and_recall_memory(self) -> None:
        offload_to_memory("arch_rule_1", "Everything in Brain Harness is a plugin.", topic="architecture")
        offload_to_memory("arch_rule_2", "ServiceKeys must be typed tokens.", topic="architecture")

        res = recall_context("plugin")
        assert res["status"] == "ok"
        assert res["count"] >= 1
        assert "Everything in Brain Harness" in res["memories"][0]["content"]
