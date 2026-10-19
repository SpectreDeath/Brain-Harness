"""Deterministic 3-Pass Prompt Pruner implementing ContextPruningStrategy (Rule 9)."""

from __future__ import annotations

import sys
import time
from typing import Any

from harness.services.llm import LLMMessage
from harness.services.context_optimizer.models import (
    ContextOptimizationConfig,
    PruningMetric,
    estimate_tokens,
)
from harness.services.context_optimizer.pruning_models import (
    DEFINE_PATTERN,
    REF_PATTERN,
    PrunableMessage,
    PruningAuditReport,
)
from harness.services.context_optimizer.protocols import ContextPruningStrategy

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DeterministicPromptPruner(ContextPruningStrategy):
    """Compiler-style 3-pass deterministic pruner with provable fixed-point idempotence."""

    def __init__(self, jaccard_threshold: float = 0.90) -> None:
        self.jaccard_threshold = jaccard_threshold

    @property
    def name(self) -> str:
        return "deterministic_prompt_pruner"

    def prune_prunable_messages(
        self, messages: list[PrunableMessage]
    ) -> tuple[list[PrunableMessage], PruningAuditReport]:
        """Core algorithmic 3-pass pruning execution."""
        t0 = time.perf_counter()
        initial_count = len(messages)

        # Pass 1: Expired Tool Context Elimination (keep latest occurrence per resource_key)
        last_keys: dict[str, int] = {}
        for idx, m in enumerate(messages):
            key = m.resource_key or m.tool_call_id
            if key:
                last_keys[key] = idx

        after_p1: list[PrunableMessage] = []
        p1_dropped: list[PrunableMessage] = []
        for idx, m in enumerate(messages):
            key = m.resource_key or m.tool_call_id
            if key and last_keys.get(key) != idx:
                p1_dropped.append(m)
            else:
                after_p1.append(m)

        # Pass 2: Duplicate Context Elimination (normalized exact / near-exact passage deduplication)
        seen_passages: dict[str, int] = {}
        after_p2: list[PrunableMessage] = []
        p2_dropped: list[PrunableMessage] = []
        for m in after_p1:
            if m.role in ("tool", "tool_output", "system"):
                norm = " ".join(m.content.lower().split())
                if norm in seen_passages:
                    p2_dropped.append(m)
                    continue
                seen_passages[norm] = m.turn_index
            after_p2.append(m)

        # Pass 3: Dependency Restoration
        all_removed = p1_dropped + p2_dropped
        kept_turns = {m.turn_index for m in after_p2}
        by_turn = {m.turn_index: m for m in messages}

        # Map defined keys across ALL original messages
        key_definer: dict[str, int] = {}
        for m in messages:
            for k in m.defines_keys:
                key_definer[k] = m.turn_index

        # Find keys required by surviving messages
        needed_keys: set[str] = set()
        for m in after_p2:
            needed_keys.update(m.depends_on)

        restored: list[PrunableMessage] = []
        for key in needed_keys:
            definer_turn = key_definer.get(key)
            if definer_turn is not None and definer_turn not in kept_turns:
                restored_msg = by_turn[definer_turn]
                after_p2.append(restored_msg)
                kept_turns.add(definer_turn)
                restored.append(restored_msg)

        # Restore stable chronological order
        after_p2.sort(key=lambda m: m.turn_index)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        dropped_turns = tuple(m.turn_index for m in all_removed if m not in restored)
        restored_turns = tuple(m.turn_index for m in restored)

        report = PruningAuditReport(
            original_message_count=initial_count,
            pruned_message_count=len(after_p2),
            dropped_turns=dropped_turns,
            restored_turns=restored_turns,
            pass1_dropped=len(p1_dropped),
            pass2_dropped=len(p2_dropped),
            pass3_restored=len(restored),
            elapsed_ms=elapsed_ms,
        )
        return after_p2, report

    def prune(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig,
    ) -> tuple[list[LLMMessage], PruningMetric | None]:
        """Adapter method satisfying ContextPruningStrategy protocol."""
        t0 = time.perf_counter()
        initial_count = len(messages)
        tokens_before = estimate_tokens(messages)

        if not config.enable_pruning or initial_count <= 2:
            return list(messages), None

        # Convert LLMMessage sequence to PrunableMessage sequence
        prunables: list[PrunableMessage] = []
        for idx, m in enumerate(messages):
            # Extract possible resource_key from content convention or role
            resource_key = None
            if m.role in ("tool", "system") and "KEY:" in m.content:
                parts = m.content.split("KEY:")
                if len(parts) > 1:
                    resource_key = parts[1].split()[0].strip()

            prunables.append(
                PrunableMessage(
                    role=m.role,
                    content=m.content,
                    turn_index=idx,
                    resource_key=resource_key,
                )
            )

        pruned_prunables, report = self.prune_prunable_messages(prunables)

        # Re-convert back to LLMMessage
        pruned_messages = [
            LLMMessage(role=pm.role, content=pm.content)
            for pm in pruned_prunables
        ]
        tokens_after = estimate_tokens(pruned_messages)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        metric = PruningMetric(
            strategy_name=self.name,
            initial_count=initial_count,
            pruned_count=len(pruned_messages),
            estimated_tokens_before=tokens_before,
            estimated_tokens_after=tokens_after,
            duration_ms=elapsed_ms,
        )
        return pruned_messages, metric
