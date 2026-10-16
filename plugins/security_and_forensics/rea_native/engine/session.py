"""Native Analysis Session Cache for REA Native Forensics.

Provides bounded in-memory LRU caching of binary headers, parsed sections,
and symbol annotations across sequential agent tool steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class NativeBinarySessionEntry:
    """Cached analysis record for an individual native binary artifact."""

    sha256: str
    file_path: str
    binary_format: str = "RAW"
    arch: str = "x86_64"
    sections: list[dict[str, Any]] = field(default_factory=list)
    imported_symbols: list[str] = field(default_factory=list)
    exported_symbols: list[str] = field(default_factory=list)
    mitigations: dict[str, Any] | None = None
    decompiled_symbols: dict[str, dict[str, Any]] = field(default_factory=dict)
    annotations: dict[str, dict[str, Any]] = field(default_factory=dict)


class NativeAnalysisSessionCache:
    """In-memory LRU cache for native binary analysis records."""

    def __init__(self, max_entries: int = 32) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, NativeBinarySessionEntry] = {}

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

    def get(self, key: str) -> NativeBinarySessionEntry | None:
        """Retrieve entry by file SHA-256 or path key."""
        return self._entries.get(key)

    def put(self, entry: NativeBinarySessionEntry) -> None:
        """Store an analysis session entry, pruning oldest if capacity reached."""
        if len(self._entries) >= self.max_entries and entry.sha256 not in self._entries:
            oldest_key = next(iter(self._entries))
            del self._entries[oldest_key]
        self._entries[entry.sha256] = entry
        # Also index by path for quick lookup
        self._entries[entry.file_path] = entry

    def get_sections(self, file_path: str | Path) -> list[dict[str, Any]] | None:
        """Retrieve cached sections if analyzed previously."""
        entry = self.get(str(file_path))
        if entry and entry.sections:
            return entry.sections
        return None

    def clear(self) -> None:
        """Clear all cached session records."""
        self._entries.clear()
