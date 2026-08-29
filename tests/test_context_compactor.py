"""Unit tests for ContextCompactorService progressive middle-out reduction and memory store."""

from __future__ import annotations

import pytest

from harness.services.context_compactor import (
    CONTEXT_COMPACTOR_KEY,
    DefaultContextCompactorService,
)


@pytest.mark.unit
def test_context_compactor_service_key() -> None:
    """Verify ServiceKey registration."""
    assert CONTEXT_COMPACTOR_KEY.name == "service.context_compactor"


@pytest.mark.unit
def test_middle_out_tool_reduction() -> None:
    """Test dropping tool observations progressively from the middle outwards."""
    svc = DefaultContextCompactorService()

    messages = [
        {"role": "system", "content": "You are Harness agent."},
        {"role": "user", "content": "Task: build a module"},
        {"role": "assistant", "content": "I will list dir"},
        {"role": "observation", "content": "tool_response: [file1, file2, file3]"},
        {"role": "assistant", "content": "I will read file1"},
        {"role": "observation", "content": "tool_response: file1 contents"},
        {"role": "assistant", "content": "I will read file2"},
        {"role": "observation", "content": "tool_response: file2 contents"},
        {"role": "assistant", "content": "I will write file3"},
        {"role": "observation", "content": "tool_response: ok"},
        {"role": "assistant", "content": "Done with task"},
    ]

    res = svc.compact_conversation(messages, preserve_recent=3, max_tool_reduction_pct=50)
    assert res.status == "ok"
    assert res.summarized is True
    assert res.compacted_count < len(messages)
    # Check that header messages are preserved
    assert res.compacted_messages[0]["content"] == "You are Harness agent."
    assert res.compacted_messages[1]["content"] == "Task: build a module." or "Task: build a module" in res.compacted_messages[1]["content"]
    # Check that summary message is inserted
    has_summary = any("CONVERSATION SUMMARY" in m["content"] for m in res.compacted_messages)
    assert has_summary is True


@pytest.mark.unit
def test_memory_offload_and_recall() -> None:
    """Test memory offloading and query recall."""
    svc = DefaultContextCompactorService()

    svc.offload_to_memory("arch_rule_1", "Always use typed ServiceKey[T] for services", topic="architecture")
    svc.offload_to_memory("git_rule_1", "Always rollback on failed context transactions", topic="git")

    res = svc.recall_context("ServiceKey registration")
    assert res.status == "ok"
    assert res.count >= 1
    assert any("ServiceKey" in m["content"] for m in res.memories)
