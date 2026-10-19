"""Tool functions and benchmarks for Prompt Pruning Layer plugin."""

from __future__ import annotations

import sys
import time
from typing import Any

import structlog

from plugins.memory_and_epistemics.prompt_pruning_layer.pruner_core import (
    WORKLOAD_CHAT,
    WORKLOAD_RAG,
    WORKLOAD_TOOL_AGENT,
    Message,
    PromptBuilder,
    PromptPruner,
    generate_corpus,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.prompt_pruning_layer")


def _dict_to_message(d: dict[str, Any], idx: int = 0) -> Message:
    return Message(
        id=str(d.get("id", f"msg_{idx}")),
        role=d.get("role", "user"),
        content=d.get("content", ""),
        turn=int(d.get("turn", idx)),
        tool_call_key=d.get("tool_call_key"),
        expires_after_turn=d.get("expires_after_turn"),
        defines_keys=list(d.get("defines_keys", [])),
    )


def prune_messages(messages: list[dict[str, Any]], assemble_prompt: bool = True) -> dict[str, Any]:
    """Run all 3 deterministic optimization passes over prompt messages before model dispatch."""
    if not messages:
        return {
            "status": "ok",
            "pruned_messages": [],
            "report": {
                "input_count": 0,
                "output_count": 0,
                "token_reduction_pct": 0.0,
            },
            "prompt_text": "",
        }

    try:
        msg_objs = [_dict_to_message(m, idx=i) for i, m in enumerate(messages)]
        pruner = PromptPruner()
        start = time.perf_counter()
        pruned_objs, report = pruner.prune(msg_objs)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

        builder = PromptBuilder()
        prompt_str = builder.build(pruned_objs) if assemble_prompt else ""

        return {
            "status": "ok",
            "pruned_messages": [m.to_dict() for m in pruned_objs],
            "report": report.to_dict(),
            "elapsed_ms": elapsed_ms,
            "prompt_text": prompt_str,
        }
    except Exception as e:
        logger.error("prune_messages_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def build_prompt(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Format and assemble a list of messages into a single prompt string ordered by turn."""
    try:
        msg_objs = [_dict_to_message(m, idx=i) for i, m in enumerate(messages)]
        builder = PromptBuilder()
        text = builder.build(msg_objs)
        return {
            "status": "ok",
            "message_count": len(msg_objs),
            "prompt_text": text,
        }
    except Exception as e:
        logger.error("build_prompt_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def estimate_prompt_reduction(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate token counts before vs after 3-pass pruning with diagnostics."""
    if not messages:
        return {
            "status": "ok",
            "tokens_before": 0,
            "tokens_after": 0,
            "tokens_saved": 0,
            "reduction_pct": 0.0,
        }

    try:
        msg_objs = [_dict_to_message(m, idx=i) for i, m in enumerate(messages)]
        pruner = PromptPruner()
        _, report = pruner.prune(msg_objs)

        return {
            "status": "ok",
            "input_messages": report.input_count,
            "output_messages": report.output_count,
            "expired_removed": report.expired_removed,
            "duplicates_removed": report.duplicates_removed,
            "restored_for_dependency": report.restored_for_dependency,
            "tokens_before": report.tokens_before,
            "tokens_after": report.tokens_after,
            "tokens_saved": max(0, report.tokens_before - report.tokens_after),
            "reduction_pct": report.token_reduction_pct,
        }
    except Exception as e:
        logger.error("estimate_prompt_reduction_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def generate_benchmark_corpus(
    num_turns: int = 100,
    workload: str = "tool_agent",
    seed: int = 42,
) -> dict[str, Any]:
    """Generate a synthetic multi-turn dialogue corpus with controlled duplicates and tool usage."""
    wl_map = {
        "chat": WORKLOAD_CHAT,
        "rag": WORKLOAD_RAG,
        "tool_agent": WORKLOAD_TOOL_AGENT,
    }
    wl_config = wl_map.get(workload, WORKLOAD_TOOL_AGENT)

    try:
        corpus = generate_corpus(num_turns=num_turns, workload=wl_config, seed=seed)
        return {
            "status": "ok",
            "workload": workload,
            "total_messages": len(corpus.messages),
            "required_ids_count": len(corpus.required_ids),
            "messages": [m.to_dict() for m in corpus.messages],
        }
    except Exception as e:
        logger.error("generate_corpus_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def benchmark_pruning_workloads(num_turns: int = 150, seed: int = 42) -> dict[str, Any]:
    """Run comparative evaluation across chat, rag, and tool_agent workloads."""
    results: dict[str, Any] = {}
    pruner = PromptPruner()

    for name, config in [("chat", WORKLOAD_CHAT), ("rag", WORKLOAD_RAG), ("tool_agent", WORKLOAD_TOOL_AGENT)]:
        corpus = generate_corpus(num_turns=num_turns, workload=config, seed=seed)
        start = time.perf_counter()
        once, report = pruner.prune(corpus.messages)
        twice, _ = pruner.prune(once)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        surviving_ids = {m.id for m in once}
        missing_required = corpus.required_ids - surviving_ids
        is_idempotent = {m.id for m in once} == {m.id for m in twice}

        results[name] = {
            "input_messages": report.input_count,
            "output_messages": report.output_count,
            "tokens_before": report.tokens_before,
            "tokens_after": report.tokens_after,
            "token_reduction_pct": report.token_reduction_pct,
            "expired_removed": report.expired_removed,
            "duplicates_removed": report.duplicates_removed,
            "restored_for_dependency": report.restored_for_dependency,
            "idempotent": is_idempotent,
            "missing_required_count": len(missing_required),
            "elapsed_ms": elapsed_ms,
        }

    return {
        "status": "ok",
        "num_turns": num_turns,
        "workloads": results,
    }
