"""Tests for Domain: Prompt Pruning Layer plugin (3-Pass Prompt Optimizer)."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.memory_and_epistemics.prompt_pruning_layer.main import (
    PromptPruningService,
    benchmark_pruning_workloads,
    build_prompt,
    estimate_prompt_reduction,
    generate_benchmark_corpus,
    prune_messages,
)
from plugins.memory_and_epistemics.prompt_pruning_layer.pruner_core import (
    ROLE_RETRIEVED_DOC,
    ROLE_TOOL_OUTPUT,
    ROLE_USER,
    Message,
    PromptBuilder,
    PromptPruner,
)


@pytest.mark.unit
class TestPromptPruningLayerPlugin:
    def test_pass1_expired_tool_elimination(self) -> None:
        messages = [
            {"id": "t1", "role": "tool_output", "content": "Initial query result", "turn": 1, "tool_call_key": "search_users"},
            {"id": "t2", "role": "tool_output", "content": "Updated query result", "turn": 2, "tool_call_key": "search_users"},
        ]
        res = prune_messages(messages)
        assert res["status"] == "ok"
        pruned_ids = [m["id"] for m in res["pruned_messages"]]
        assert "t1" not in pruned_ids
        assert "t2" in pruned_ids
        assert res["report"]["expired_removed"] == 1

    def test_pass2_duplicate_passage_elimination(self) -> None:
        messages = [
            {"id": "d1", "role": "retrieved_doc", "content": "System documentation on auth.", "turn": 1},
            {"id": "d2", "role": "retrieved_doc", "content": "system DOCUMENTATION on auth.", "turn": 2},
        ]
        res = prune_messages(messages)
        assert res["status"] == "ok"
        pruned_ids = [m["id"] for m in res["pruned_messages"]]
        assert "d1" in pruned_ids
        assert "d2" not in pruned_ids
        assert res["report"]["duplicates_removed"] == 1

    def test_pass3_dependency_restoration(self) -> None:
        # t1 is expired by t2, but t1 contains DEFINE:token_schema referenced by u1
        messages = [
            {"id": "t1", "role": "tool_output", "content": "Token specs DEFINE:token_schema", "turn": 1, "tool_call_key": "specs"},
            {"id": "t2", "role": "tool_output", "content": "Newer specs", "turn": 2, "tool_call_key": "specs"},
            {"id": "u1", "role": "user", "content": "Please validate REF:token_schema", "turn": 3},
        ]
        res = prune_messages(messages)
        assert res["status"] == "ok"
        pruned_ids = [m["id"] for m in res["pruned_messages"]]
        assert "t1" in pruned_ids  # Restored!
        assert "t2" in pruned_ids
        assert "u1" in pruned_ids
        assert res["report"]["restored_for_dependency"] == 1

    def test_idempotence_property(self) -> None:
        messages = [
            {"id": "t1", "role": "tool_output", "content": "old", "turn": 1, "tool_call_key": "k"},
            {"id": "t2", "role": "tool_output", "content": "new", "turn": 2, "tool_call_key": "k"},
            {"id": "d1", "role": "retrieved_doc", "content": "Same doc.", "turn": 1},
            {"id": "d2", "role": "retrieved_doc", "content": "same DOC.", "turn": 2},
        ]
        res1 = prune_messages(messages)
        res2 = prune_messages(res1["pruned_messages"])
        assert [m["id"] for m in res1["pruned_messages"]] == [m["id"] for m in res2["pruned_messages"]]

    def test_build_prompt_and_reduction_estimate(self) -> None:
        messages = [
            {"id": "u1", "role": "user", "content": "Hello", "turn": 1},
            {"id": "a1", "role": "assistant", "content": "Hi there!", "turn": 2},
        ]
        built = build_prompt(messages)
        assert built["status"] == "ok"
        assert "[USER] Hello" in built["prompt_text"]
        assert "[ASSISTANT] Hi there!" in built["prompt_text"]

        est = estimate_prompt_reduction(messages)
        assert est["status"] == "ok"
        assert est["input_messages"] == 2

    def test_corpus_generator_and_benchmark(self) -> None:
        corpus = generate_benchmark_corpus(num_turns=20, workload="tool_agent", seed=42)
        assert corpus["status"] == "ok"
        assert corpus["total_messages"] > 20

        bench = benchmark_pruning_workloads(num_turns=30, seed=42)
        assert bench["status"] == "ok"
        assert "chat" in bench["workloads"]
        assert "rag" in bench["workloads"]
        assert "tool_agent" in bench["workloads"]
        assert bench["workloads"]["tool_agent"]["idempotent"] is True

    def test_service_facade(self) -> None:
        svc = PromptPruningService()
        res = svc.build([{"role": "user", "content": "test"}])
        assert res["status"] == "ok"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/memory_and_epistemics/prompt_pruning_layer")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0
