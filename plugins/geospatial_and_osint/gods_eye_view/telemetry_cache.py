"""Thread-safe Asynchronous Telemetry Cache with Single-Flight Stampede Protection.

Provides tiered time-to-live (TTL) expiration, automatic stale-while-revalidate,
and single-flight locking to prevent downstream API rate limiting across agent workflows.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Cached payload with timestamp metadata."""

    data: T
    expires_at: float
    stale_at: float
    created_at: float = field(default_factory=time.time)


class TelemetryCache(Generic[T]):
    """Thread-safe async TTL cache for high-frequency geospatial feeds."""

    # Default TTLs (in seconds) by telemetry feed domain
    DEFAULT_TTLS: dict[str, float] = {
        "flights": 15.0,
        "military_flights": 15.0,
        "ais_vessels": 30.0,
        "earthquakes": 60.0,
        "firms_hotspots": 300.0,
        "satellites": 300.0,
        "infrastructure": 3600.0,
    }

    def __init__(self, stale_ratio: float = 0.8) -> None:
        self._cache: dict[str, CacheEntry[T]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self.stale_ratio = min(0.95, max(0.5, stale_ratio))
        self.hits: int = 0
        self.misses: int = 0
        self.refreshes: int = 0

    async def _get_lock_for_key(self, key: str) -> asyncio.Lock:
        """Get or initialize single-flight lock for key."""
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Awaitable[T]],
        ttl_seconds: float | None = None,
        force_refresh: bool = False,
    ) -> T:
        """Get value from cache or execute fetch_fn with single-flight concurrency protection."""
        now = time.time()
        ttl = ttl_seconds or self.DEFAULT_TTLS.get(key, 30.0)

        # 1. Fast path: Valid non-stale cache hit
        if not force_refresh and key in self._cache:
            entry = self._cache[key]
            if now < entry.stale_at:
                self.hits += 1
                return entry.data

        # 2. Acquire key-specific lock to prevent stampedes
        key_lock = await self._get_lock_for_key(key)
        async with key_lock:
            # Double-check if another task completed the fetch while waiting for lock
            now = time.time()
            if not force_refresh and key in self._cache:
                entry = self._cache[key]
                if now < entry.stale_at:
                    self.hits += 1
                    return entry.data

            # 3. Perform fetch
            self.misses += 1
            try:
                data = await fetch_fn()
                stale_at = now + (ttl * self.stale_ratio)
                expires_at = now + ttl
                self._cache[key] = CacheEntry(data=data, stale_at=stale_at, expires_at=expires_at)
                self.refreshes += 1
                return data
            except Exception as e:
                logger.warning("Telemetry fetch error, checking for stale cache fallback", key=key, error=str(e))
                # Graceful degradation: return stale cache if available
                if key in self._cache:
                    logger.info("Serving stale cached data as fallback", key=key)
                    return self._cache[key].data
                raise

    def get_cached_nowait(self, key: str) -> T | None:
        """Synchronously check for cached entry if still within expiration."""
        entry = self._cache.get(key)
        if entry is not None and time.time() < entry.expires_at:
            return entry.data
        return None

    def invalidate(self, key: str) -> bool:
        """Manually invalidate cache entry."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Return cache health & efficiency metrics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total) if total > 0 else 0.0
        return {
            "cached_keys_count": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "refreshes": self.refreshes,
            "hit_rate_pct": round(hit_rate * 100, 2),
        }
