"""Semantic Cache Plugin for Brain Harness.

Provides similarity-based caching for LLM prompts and computational results,
reducing redundant token costs and latency across agent workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import time
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

SEMANTIC_CACHE_KEY: ServiceKey[SemanticCacheService] = ServiceKey("memory.semantic_cache")


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase word tokens."""
    return set(re.findall(r"\w+", text.lower()))


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two token sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


@dataclass
class CacheEntry:
    prompt: str
    response: str
    tokens: set[str]
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    hit_count: int = 0


class SemanticCacheService:
    """In-memory semantic prompt/response cache with similarity lookup and TTL eviction."""

    def __init__(self, default_ttl: float = 3600.0, max_entries: int = 1000) -> None:
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._entries: list[CacheEntry] = []
        self._hits = 0
        self._misses = 0

    def set(
        self,
        prompt: str,
        response: str,
        *,
        ttl: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store a prompt and its response in the cache."""
        self._evict_expired()

        tokens = _tokenize(prompt)
        entry_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + entry_ttl if entry_ttl > 0 else None

        # Check if identical prompt exists
        for e in self._entries:
            if e.prompt == prompt:
                e.response = response
                e.expires_at = expires_at
                e.metadata = metadata or {}
                return True

        # Evict LRU if at capacity
        if len(self._entries) >= self.max_entries:
            self._entries.pop(0)

        self._entries.append(
            CacheEntry(
                prompt=prompt,
                response=response,
                tokens=tokens,
                expires_at=expires_at,
                metadata=metadata or {},
            )
        )
        return True

    def get(
        self,
        prompt: str,
        *,
        similarity_threshold: float = 0.90,
    ) -> dict[str, Any] | None:
        """Lookup response by prompt similarity."""
        self._evict_expired()
        query_tokens = _tokenize(prompt)

        best_match: CacheEntry | None = None
        best_similarity = 0.0

        for entry in self._entries:
            sim = _jaccard_similarity(query_tokens, entry.tokens)
            if sim > best_similarity:
                best_similarity = sim
                best_match = entry

        if best_match is not None and best_similarity >= similarity_threshold:
            self._hits += 1
            best_match.hit_count += 1
            logger.debug(
                "Semantic cache hit",
                similarity=round(best_similarity, 3),
                hit_count=best_match.hit_count,
            )
            return {
                "hit": True,
                "similarity": round(best_similarity, 3),
                "matched_prompt": best_match.prompt,
                "response": best_match.response,
                "metadata": best_match.metadata,
                "created_at": best_match.created_at,
            }

        self._misses += 1
        return None

    def stats(self) -> dict[str, Any]:
        """Return cache performance statistics."""
        self._evict_expired()
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0
        return {
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
        }

    def clear(self) -> None:
        """Clear all cached entries."""
        self._entries.clear()
        self._hits = 0
        self._misses = 0

    def _evict_expired(self) -> None:
        """Remove entries whose TTL has passed."""
        now = time.time()
        self._entries = [
            e for e in self._entries if e.expires_at is None or e.expires_at > now
        ]


_cache_instance = SemanticCacheService()


def cache_set(prompt: str, response: str, ttl: float = 3600.0) -> dict[str, Any]:
    """Cache a prompt response pair."""
    ok = _cache_instance.set(prompt, response, ttl=ttl)
    return {"status": "ok", "saved": ok}


def cache_get(prompt: str, similarity_threshold: float = 0.90) -> dict[str, Any]:
    """Retrieve a cached response if similarity >= threshold."""
    res = _cache_instance.get(prompt, similarity_threshold=similarity_threshold)
    if res is not None:
        return {"status": "hit", **res}
    return {"status": "miss", "hit": False, "similarity": 0.0}


def cache_stats() -> dict[str, Any]:
    """Return cache statistics."""
    return {"status": "ok", **_cache_instance.stats()}


def cache_clear() -> dict[str, Any]:
    """Clear the cache."""
    _cache_instance.clear()
    return {"status": "ok", "cleared": True}


class SemanticCachePlugin(HarnessPlugin):
    """Plugin providing semantic response caching capabilities."""

    @property
    def name(self) -> str:
        return "plugin.semantic_cache"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Similarity-based semantic cache for LLM prompts and agent task results"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SEMANTIC_CACHE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SEMANTIC_CACHE_KEY, _cache_instance, provider=self.name)
        logger.info("SemanticCacheService provided", plugin=self.name)
