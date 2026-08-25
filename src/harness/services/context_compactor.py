"""Context Compactor and Memory Offloading protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class CompactConversationResult(BaseModel):
    """Result of compacting conversation messages."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    original_count: int = Field(default=0, description="Original message count")
    compacted_count: int = Field(default=0, description="Compacted message count")
    summarized: bool = Field(default=False, description="Whether prior turns were condensed")
    condensed_turns: int = Field(default=0, description="Number of turns summarized")
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
