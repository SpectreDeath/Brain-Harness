"""Context compactor and Memtext memory offloading plugin."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.context_compactor import (
    CONTEXT_COMPACTOR_KEY,
    CompactConversationResult,
    ContextCompactorService,
    OffloadMemoryResult,
    RecallMemoryResult,
)

logger = structlog.get_logger(__name__)


class ContextCompactorEngine:
    """Encapsulated engine for conversation compaction and fallback memory offloading."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def compact_conversation(
        self,
        messages: list[dict[str, Any]],
        preserve_recent: int = 4,
    ) -> dict[str, Any]:
        if not messages:
            return {"status": "ok", "compacted_messages": [], "original_count": 0, "compacted_count": 0, "summarized": False, "condensed_turns": 0}

        total = len(messages)
        if total <= preserve_recent + 1:
            return {
                "status": "ok",
                "compacted_messages": messages,
                "original_count": total,
                "compacted_count": total,
                "summarized": False,
                "condensed_turns": 0,
            }

        system_msg = messages[0] if messages[0].get("role") == "system" else None
        start_idx = 1 if system_msg else 0

        older_messages = messages[start_idx : total - preserve_recent]
        recent_messages = messages[total - preserve_recent :]

        summary_bullets: list[str] = []
        for msg in older_messages:
            role = msg.get("role", "unknown")
            content = str(msg.get("content", "")).strip()
            snippet = content[:150] + "..." if len(content) > 150 else content
            summary_bullets.append(f"- **{role.capitalize()}**: {snippet}")

        digest_content = (
            "[CONTEXT SUMMARY - Prior conversation history condensed to save tokens]:\n"
            + "\n".join(summary_bullets)
        )

        compacted: list[dict[str, Any]] = []
        if system_msg:
            compacted.append(system_msg)
        compacted.append({"role": "system", "content": digest_content})
        compacted.extend(recent_messages)

        return {
            "status": "ok",
            "original_count": total,
            "compacted_count": len(compacted),
            "summarized": True,
            "condensed_turns": len(older_messages),
            "compacted_messages": compacted,
        }

    def offload_to_memory(
        self,
        key: str,
        content: str,
        topic: str = "general",
    ) -> dict[str, Any]:
        self._store[key] = {
            "key": key,
            "content": content,
            "topic": topic,
        }
        logger.info("Context offloaded to memory", key=key, topic=topic)
        return {"status": "ok", "key": key, "topic": topic}

    def recall_context(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_lower = query.lower()
        matches = []
        for item in self._store.values():
            if query_lower in item["key"].lower() or query_lower in item["content"].lower():
                matches.append(item)
                if len(matches) >= limit:
                    break

        return {"status": "ok", "count": len(matches), "memories": matches}


_GLOBAL_ENGINE = ContextCompactorEngine()


def compact_conversation(
    messages: list[dict[str, Any]],
    preserve_recent: int = 4,
) -> dict[str, Any]:
    """Compress older conversation turns while keeping recent interactions intact."""
    return _GLOBAL_ENGINE.compact_conversation(messages=messages, preserve_recent=preserve_recent)


def offload_to_memory(
    key: str,
    content: str,
    topic: str = "general",
) -> dict[str, Any]:
    """Store fact or observation into memory."""
    return _GLOBAL_ENGINE.offload_to_memory(key=key, content=content, topic=topic)


def recall_context(query: str, limit: int = 5) -> dict[str, Any]:
    """Search and recall relevant memories."""
    return _GLOBAL_ENGINE.recall_context(query=query, limit=limit)


class ContextCompactorPlugin(HarnessPlugin, ContextCompactorService):
    """Harness Plugin providing conversation compaction and memory offloading services."""

    name = "plugin.context_compactor"
    version = "1.0.0"
    description = "Conversation compactor, token window optimizer, and memory offload service"
    trusted = True

    def __init__(self, engine: ContextCompactorEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CONTEXT_COMPACTOR_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(CONTEXT_COMPACTOR_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # ContextCompactorService Protocol Implementation
    # -------------------------------------------------------------------------

    def compact_conversation(
        self,
        messages: list[dict[str, Any]],
        preserve_recent: int = 4,
    ) -> CompactConversationResult:
        res = self._engine.compact_conversation(messages=messages, preserve_recent=preserve_recent)
        return CompactConversationResult(
            status=res["status"],
            original_count=res.get("original_count", 0),
            compacted_count=res.get("compacted_count", 0),
            summarized=res.get("summarized", False),
            condensed_turns=res.get("condensed_turns", 0),
            compacted_messages=res.get("compacted_messages", []),
            error=res.get("error"),
        )

    def offload_to_memory(
        self,
        key: str,
        content: str,
        topic: str = "general",
    ) -> OffloadMemoryResult:
        res = self._engine.offload_to_memory(key=key, content=content, topic=topic)
        return OffloadMemoryResult(
            status=res["status"],
            key=res.get("key", key),
            topic=res.get("topic", topic),
            error=res.get("error"),
        )

    def recall_context(self, query: str, limit: int = 5) -> RecallMemoryResult:
        res = self._engine.recall_context(query=query, limit=limit)
        return RecallMemoryResult(
            status=res["status"],
            count=res.get("count", 0),
            memories=res.get("memories", []),
            error=res.get("error"),
        )
