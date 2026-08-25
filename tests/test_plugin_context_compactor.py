"""Tests for context_compactor plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.context_compactor import (
    CONTEXT_COMPACTOR_KEY,
    CompactConversationResult,
    ContextCompactorService,
    OffloadMemoryResult,
    RecallMemoryResult,
)
from plugins.memory_and_epistemics.context_compactor.main import (
    ContextCompactorPlugin,
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

    @pytest.mark.asyncio
    async def test_context_compactor_plugin_ioc_lifecycle(self) -> None:
        plugin = ContextCompactorPlugin()
        assert plugin.name == "plugin.context_compactor"
        assert CONTEXT_COMPACTOR_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(CONTEXT_COMPACTOR_KEY)
        assert isinstance(service, ContextCompactorService)

        offload_res = service.offload_to_memory("rule_ioc", "IoC container resolves typed keys", topic="ioc")
        assert isinstance(offload_res, OffloadMemoryResult)
        assert offload_res.status == "ok"

        recall_res = service.recall_context("container")
        assert isinstance(recall_res, RecallMemoryResult)
        assert recall_res.count >= 1

        compact_res = service.compact_conversation([
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
        ])
        assert isinstance(compact_res, CompactConversationResult)
        assert compact_res.status == "ok"

        await plugin.on_disable()
        await plugin.on_unload()
