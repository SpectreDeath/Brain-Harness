"""Semantic Cache Plugin for Brain Harness.

Provides similarity-based caching for LLM prompts and computational results,
reducing redundant token costs and latency across agent workflows.
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.semantic_cache import (
    SEMANTIC_CACHE_KEY,
    CacheClearResult,
    CacheEntry,
    CacheGetResult,
    CacheSetResult,
    CacheStatsResult,
    SemanticCacheService,
)

logger = structlog.get_logger(__name__)

# Global default instance
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

    name = "plugin.semantic_cache"
    version = "1.0.0"
    description = "Similarity-based semantic cache for LLM prompts and agent task results"
    trusted = True

    def __init__(self, service: SemanticCacheService | None = None) -> None:
        self._service = service or _cache_instance

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SEMANTIC_CACHE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SEMANTIC_CACHE_KEY, self._service, provider=self.name)
        logger.info("SemanticCacheService provided", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("SemanticCachePlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("SemanticCachePlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("SemanticCachePlugin unloaded", plugin=self.name)
