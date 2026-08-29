"""Context Compactor and Memory Offloading protocol, typed models, and ServiceKey."""

from __future__ import annotations

import re
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()


class CompactConversationResult(BaseModel):
    """Result of compacting conversation messages."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    original_count: int = Field(default=0, description="Original message count")
    compacted_count: int = Field(default=0, description="Compacted message count")
    summarized: bool = Field(default=False, description="Whether prior turns were condensed")
    condensed_turns: int = Field(default=0, description="Number of turns summarized")
    reduction_percentage: int = Field(default=0, description="Percentage of tool outputs dropped")
    compacted_messages: list[dict[str, Any]] = Field(default_factory=list, description="Preserved and compacted messages")
    error: str | None = Field(default=None, description="Error explanation if compaction failed")


class OffloadMemoryResult(BaseModel):
    """Result of offloading a fact or observation to memory."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    key: str = Field(..., description="Unique memory key")
    topic: str = Field(default="general", description="Topic or category classification")
    error: str | None = Field(default=None, description="Error explanation if offload failed")


class RecallMemoryResult(BaseModel):
    """Result of searching and recalling memories."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    count: int = Field(default=0, description="Number of matching memories recalled")
    memories: list[dict[str, Any]] = Field(default_factory=list, description="Recalled memory entries")
    error: str | None = Field(default=None, description="Error explanation if recall failed")


@runtime_checkable
class ContextCompactorService(Protocol):
    """Protocol for conversation compaction, token budgeting, and fact offloading."""

    def compact_conversation(
        self,
        messages: list[dict[str, Any]],
        preserve_recent: int = 4,
        max_tool_reduction_pct: int = 50,
    ) -> CompactConversationResult:
        """Compress older conversation turns while keeping recent interactions intact."""
        ...

    def offload_to_memory(
        self,
        key: str,
        content: str,
        topic: str = "general",
    ) -> OffloadMemoryResult:
        """Store fact or observation into persistent/fallback memory."""
        ...

    def recall_context(self, query: str, limit: int = 5) -> RecallMemoryResult:
        """Search and recall relevant memories matching query terms."""
        ...


CONTEXT_COMPACTOR_KEY: ServiceKey[ContextCompactorService] = ServiceKey("service.context_compactor")


class DefaultContextCompactorService:
    """Default implementation of ContextCompactorService with progressive middle-out reduction."""

    REDUCTION_STAGES: list[int] = [0, 10, 20, 50, 100]

    def __init__(self) -> None:
        self._memory_store: dict[str, dict[str, Any]] = {}

    def _is_tool_message(self, msg: dict[str, Any]) -> bool:
        role = str(msg.get("role", "")).lower()
        if role in {"tool", "observation"}:
            return True
        content = str(msg.get("content", ""))
        return content.startswith("Observation:") or content.startswith("tool_response:")

    def _filter_tool_responses_middle_out(
        self,
        messages: list[dict[str, Any]],
        remove_percent: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Drop tool responses progressively from the middle outwards (Goose algorithm)."""
        if remove_percent == 0:
            return list(messages), 0

        tool_indices = [i for i, m in enumerate(messages) if self._is_tool_message(m)]
        if not tool_indices:
            return list(messages), 0

        num_to_remove = max(1, (len(tool_indices) * remove_percent) // 100)
        middle = len(tool_indices) // 2

        # Select indices expanding outward from middle
        indices_to_drop: set[int] = set()
        for i in range(num_to_remove):
            offset = i // 2
            idx = middle - offset if i % 2 == 0 else middle + offset + 1
            if 0 <= idx < len(tool_indices):
                indices_to_drop.add(tool_indices[idx])

        filtered: list[dict[str, Any]] = []
        for i, msg in enumerate(messages):
            if i in indices_to_drop:
                # Replace with condensed marker
                filtered.append({
                    "role": msg.get("role", "system"),
                    "content": "[OBSERVATION PRUNED FOR CONTEXT BUDGET]",
                })
            else:
                filtered.append(msg)

        return filtered, len(indices_to_drop)

    def compact_conversation(
        self,
        messages: list[dict[str, Any]],
        preserve_recent: int = 4,
        max_tool_reduction_pct: int = 50,
    ) -> CompactConversationResult:
        """Progressively compact conversation using middle-out tool drop and summary blocks."""
        if not messages:
            return CompactConversationResult(status="ok", original_count=0, compacted_count=0)

        original_count = len(messages)
        if original_count <= 2 + preserve_recent:
            return CompactConversationResult(
                status="ok",
                original_count=original_count,
                compacted_count=original_count,
                compacted_messages=list(messages),
            )

        # 1. Apply middle-out tool reduction
        effective_pct = max_tool_reduction_pct if max_tool_reduction_pct in self.REDUCTION_STAGES else 50
        filtered_msgs, dropped_count = self._filter_tool_responses_middle_out(messages, effective_pct)

        # 2. Window preservation: First 2 turns (system / initial task) + Last N turns
        header = filtered_msgs[:2]
        tail_count = max(2, preserve_recent)
        tail = filtered_msgs[-tail_count:]

        if len(header) + len(tail) >= len(filtered_msgs):
            return CompactConversationResult(
                status="ok",
                original_count=original_count,
                compacted_count=len(filtered_msgs),
                reduction_percentage=effective_pct if dropped_count > 0 else 0,
                compacted_messages=filtered_msgs,
            )

        middle_msgs = filtered_msgs[len(header) : -len(tail)]
        condensed_count = len(middle_msgs)

        # Build structured condensation block
        summary_msg = {
            "role": "system",
            "content": f"[CONVERSATION SUMMARY: {condensed_count} earlier steps and reasoning turns condensed to preserve context budget]",
        }

        compacted = [*header, summary_msg, *tail]

        return CompactConversationResult(
            status="ok",
            original_count=original_count,
            compacted_count=len(compacted),
            summarized=True,
            condensed_turns=condensed_count,
            reduction_percentage=effective_pct,
            compacted_messages=compacted,
        )

    def offload_to_memory(
        self,
        key: str,
        content: str,
        topic: str = "general",
    ) -> OffloadMemoryResult:
        self._memory_store[key] = {
            "key": key,
            "content": content,
            "topic": topic,
        }
        return OffloadMemoryResult(status="ok", key=key, topic=topic)

    def recall_context(self, query: str, limit: int = 5) -> RecallMemoryResult:
        query_tokens = set(re.findall(r"[A-Za-z0-9_]{3,}", query.lower()))
        matched: list[dict[str, Any]] = []

        for item in self._memory_store.values():
            text = (item["key"] + " " + item["content"] + " " + item["topic"]).lower()
            if any(t in text for t in query_tokens) or query.lower() in text:
                matched.append(item)
                if len(matched) >= limit:
                    break

        return RecallMemoryResult(
            status="ok",
            count=len(matched),
            memories=matched,
        )


__all__ = [
    "CONTEXT_COMPACTOR_KEY",
    "CompactConversationResult",
    "ContextCompactorService",
    "DefaultContextCompactorService",
    "OffloadMemoryResult",
    "RecallMemoryResult",
]
