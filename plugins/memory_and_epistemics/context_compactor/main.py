"""Context compactor and Memtext memory offloading plugin."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()

# In-memory local fallback store when Memtext bridge is not yet active
_LOCAL_FALLBACK_STORE: dict[str, dict[str, Any]] = {}


def compact_conversation(
    messages: list[dict[str, Any]],
    preserve_recent: int = 4,
) -> dict[str, Any]:
    """Compress older conversation turns while keeping recent interactions intact."""
    if not messages:
        return {"status": "ok", "compacted_messages": [], "original_count": 0, "compacted_count": 0}

    total = len(messages)
    if total <= preserve_recent + 1:
        return {
            "status": "ok",
            "compacted_messages": messages,
            "original_count": total,
            "compacted_count": total,
            "summarized": False,
        }

    # Extract system prompt if present
    system_msg = messages[0] if messages[0].get("role") == "system" else None
    start_idx = 1 if system_msg else 0

    older_messages = messages[start_idx : total - preserve_recent]
    recent_messages = messages[total - preserve_recent :]

    # Synthesize digest of older interactions
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
    key: str,
    content: str,
    topic: str = "general",
) -> dict[str, Any]:
    """Store fact or observation into memory."""
    _LOCAL_FALLBACK_STORE[key] = {
        "key": key,
        "content": content,
        "topic": topic,
    }
    logger.info("Context offloaded to memory", key=key, topic=topic)
    return {"status": "ok", "key": key, "topic": topic}


def recall_context(query: str, limit: int = 5) -> dict[str, Any]:
    """Search and recall relevant memories."""
    query_lower = query.lower()
    matches = []
    for item in _LOCAL_FALLBACK_STORE.values():
        if query_lower in item["key"].lower() or query_lower in item["content"].lower():
            matches.append(item)
            if len(matches) >= limit:
                break

    return {"status": "ok", "count": len(matches), "memories": matches}
