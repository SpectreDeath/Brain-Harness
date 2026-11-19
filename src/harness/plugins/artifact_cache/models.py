"""Slotted immutable records and venv/filesystem helpers for plugin artifact caching."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time


@dataclass(slots=True, frozen=True)
class ArtifactCacheEntry:
    """Immutable metadata record for a cached lazily-staged plugin artifact."""

    key: str
    path: Path
    size_bytes: int
    created_at: float
    ttl_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Artifact key cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

    def is_expired(self, now: float | None = None) -> bool:
        """Return True when a configured TTL has elapsed."""
        if self.ttl_seconds is None:
            return False
        current = time.monotonic() if now is None else now
        return (current - self.created_at) >= self.ttl_seconds


@dataclass(slots=True, frozen=True)
class ArtifactOffsetRecord:
    """Immutable byte-range record for O(1) offset-indexed bundle reads (Rule 48)."""

    artifact_id: str
    offset: int
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id cannot be empty")
        if self.offset < 0 or self.size_bytes < 0:
            raise ValueError("offset and size_bytes must be non-negative")


def venv_python_path(venv_dir: Path) -> Path:
    """Return the platform-specific Python binary path inside a virtualenv."""
    scripts_dir = "Scripts" if sys.platform == "win32" else "bin"
    binary_name = "python.exe" if sys.platform == "win32" else "python"
    return venv_dir / scripts_dir / binary_name


def is_venv_healthy(venv_dir: Path) -> bool:
    """Verify the staged virtualenv Python binary exists and is non-empty."""
    py_bin = venv_python_path(venv_dir)
    try:
        return py_bin.is_file() and py_bin.stat().st_size > 0
    except OSError:
        return False


def estimate_dir_bytes(root: Path) -> int:
    """Sum file byte sizes under ``root`` safely without following symlinks."""
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    total = 0
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        for fname in filenames:
            try:
                total += (base / fname).stat(follow_symlinks=False).st_size
            except OSError:
                continue
    return total
