"""Thread-safe dual-capped OrderedDict LRU cache for lazily-staged plugin artifacts."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path
import threading
import time

from .models import ArtifactCacheEntry


class PluginArtifactCache:
    """Thread-safe OrderedDict LRU enforcing max_entries, max_size_bytes, TTL, and health checks."""

    def __init__(
        self,
        *,
        max_entries: int = 16,
        max_size_bytes: int = 512 * 1024 * 1024,
        clock: Callable[[], float] = time.monotonic,
        on_evict: Callable[[ArtifactCacheEntry], None] | None = None,
        health_check: Callable[[ArtifactCacheEntry], bool] | None = None,
    ) -> None:
        if max_entries <= 0 or max_size_bytes <= 0:
            raise ValueError("max_entries and max_size_bytes must be positive")
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._clock = clock
        self._on_evict = on_evict
        self._health_check = health_check
        self._lock = threading.RLock()
        self._entries: OrderedDict[str, ArtifactCacheEntry] = OrderedDict()
        self._total_bytes = 0
        self._evictions = 0
        self._skipped_oversized = 0

    @property
    def entry_count(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def total_bytes(self) -> int:
        with self._lock:
            return self._total_bytes

    @property
    def evictions(self) -> int:
        with self._lock:
            return self._evictions

    @property
    def skipped_oversized(self) -> int:
        with self._lock:
            return self._skipped_oversized

    @property
    def keys(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._entries.keys())

    def _notify_evicted(self, evicted: list[ArtifactCacheEntry]) -> None:
        if self._on_evict is not None:
            for item in evicted:
                self._on_evict(item)

    def put(self, key: str, path: Path, size_bytes: int, *, ttl_seconds: float | None = None) -> bool:
        """Insert or update an artifact entry; returns False when oversized without thrashing."""
        entry = ArtifactCacheEntry(
            key=key,
            path=Path(path),
            size_bytes=size_bytes,
            created_at=self._clock(),
            ttl_seconds=ttl_seconds,
        )
        if entry.size_bytes > self._max_size_bytes:
            with self._lock:
                self._skipped_oversized += 1
            return False
        evicted: list[ArtifactCacheEntry] = []
        with self._lock:
            prev = self._entries.pop(key, None)
            if prev is not None:
                self._total_bytes -= prev.size_bytes
            while self._entries and (
                len(self._entries) >= self._max_entries
                or self._total_bytes + entry.size_bytes > self._max_size_bytes
            ):
                _, victim = self._entries.popitem(last=False)
                self._total_bytes -= victim.size_bytes
                self._evictions += 1
                evicted.append(victim)
            self._entries[key] = entry
            self._total_bytes += entry.size_bytes
        self._notify_evicted(evicted)
        return True

    def get(self, key: str) -> ArtifactCacheEntry | None:
        """Fetch an entry and promote it to MRU, invalidating if expired or unhealthy."""
        evicted: list[ArtifactCacheEntry] = []
        result: ArtifactCacheEntry | None = None
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                healthy = self._health_check(entry) if self._health_check is not None else True
                if entry.is_expired(now) or not healthy:
                    self._entries.pop(key, None)
                    self._total_bytes -= entry.size_bytes
                    self._evictions += 1
                    evicted.append(entry)
                else:
                    self._entries.move_to_end(key)
                    result = entry
        self._notify_evicted(evicted)
        return result

    def invalidate(self, key: str) -> bool:
        """Explicitly remove an entry and invoke any eviction hook."""
        with self._lock:
            entry = self._entries.pop(key, None)
            if entry is None:
                return False
            self._total_bytes -= entry.size_bytes
        self._notify_evicted([entry])
        return True

    def purge_expired(self) -> int:
        """Evict all entries whose TTL has elapsed."""
        now = self._clock()
        evicted: list[ArtifactCacheEntry] = []
        with self._lock:
            for k in [k for k, v in self._entries.items() if v.is_expired(now)]:
                victim = self._entries.pop(k)
                self._total_bytes -= victim.size_bytes
                self._evictions += 1
                evicted.append(victim)
        self._notify_evicted(evicted)
        return len(evicted)
