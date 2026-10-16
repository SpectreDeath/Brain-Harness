"""Mobile Analysis Session Cache for REA Mobile & Firmware Forensics.

Provides bounded in-memory LRU caching of parsed APK descriptors,
extracted DEX class listings, and decompilation metadata across sequential agent tool steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class ApkSessionEntry:
    """Cached analysis record for an individual APK artifact."""

    sha256: str
    file_path: str
    manifest: dict[str, Any] | None = None
    classes: list[str] = field(default_factory=list)
    classes_count: int = 0
    resources_count: int = 0
    is_signed: bool = True
    decompiled_dir: str | None = None


class MobileAnalysisSessionCache:
    """In-memory cache for APK and mobile binary analysis state."""

    def __init__(self, max_entries: int = 32) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, ApkSessionEntry] = {}

    @staticmethod
    def compute_sha256(file_path: str | Path) -> str:
        """Compute SHA-256 hex digest for an input binary."""
        p = Path(file_path)
        if not p.exists():
            return ""
        hasher = hashlib.sha256()
        with p.open("rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get(self, key: str) -> ApkSessionEntry | None:
        """Retrieve entry by file SHA-256 or path key."""
        return self._entries.get(key)

    def put(self, entry: ApkSessionEntry) -> None:
        """Store an analysis session entry, pruning oldest if capacity reached."""
        if len(self._entries) >= self.max_entries and entry.sha256 not in self._entries:
            oldest_key = next(iter(self._entries))
            del self._entries[oldest_key]
        self._entries[entry.sha256] = entry
        # Also index by path for convenience
        self._entries[entry.file_path] = entry

    def get_classes(self, file_path: str | Path) -> list[str] | None:
        """Retrieve cached classes if analyzed previously."""
        entry = self.get(str(file_path))
        if entry:
            return entry.classes
        return None

    def clear(self) -> None:
        """Clear all cached session records."""
        self._entries.clear()
