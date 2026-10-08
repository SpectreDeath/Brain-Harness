"""Cross-Platform Advisory File Locking & Append-Only JSONL Session Journal Manager."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from harness.services.tau_bridge.models import SessionNode

logger = structlog.get_logger(__name__)

# Cross-platform advisory file locking imports
_HAS_FCNTL = False
_HAS_MSVCRT = False

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:
    pass

try:
    import msvcrt

    _HAS_MSVCRT = True
except ImportError:
    pass


def _parse_entry_to_node(entry: SessionNode | dict[str, Any]) -> SessionNode:
    """Helper to parse a dictionary or SessionNode into an immutable SessionNode."""
    if isinstance(entry, SessionNode):
        return entry
    tool_calls = tuple(entry.get("tool_calls") or ())
    return SessionNode(
        id=str(entry.get("id", "")),
        parent_id=entry.get("parent_id"),
        type=str(entry.get("type", "message")),
        role=str(entry.get("role", "user")),
        content=str(entry.get("content", "")),
        tool_calls=tool_calls,
        tool_call_id=entry.get("tool_call_id"),
        timestamp=str(entry.get("timestamp", "")),
    )


class SessionJournalManager:
    """Manages append-only JSONL session journals with advisory file locking."""

    @classmethod
    @contextlib.contextmanager
    def locked_file(cls, path: Path, mode: str) -> Generator[Any, None, None]:
        """Context manager providing non-blocking advisory file locking."""
        path.parent.mkdir(parents=True, exist_ok=True)
        f = open(path, mode, encoding="utf-8")  # noqa: SIM115
        locked = False
        try:
            if _HAS_FCNTL:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                except (BlockingIOError, OSError):
                    # Advisory fallback: lock contention or non-supported FS
                    pass
            elif _HAS_MSVCRT:
                try:
                    # Lock first byte non-blocking
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                except OSError:
                    pass
            yield f
        finally:
            if locked:
                try:
                    if _HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    elif _HAS_MSVCRT:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
            f.close()

    @classmethod
    def append_entry(
        cls, journal_path: str | Path, entry: SessionNode | dict[str, Any]
    ) -> SessionNode:
        """Atomically append a session entry to the locked JSONL journal."""
        p = Path(journal_path)
        node = _parse_entry_to_node(entry)
        if not node.timestamp:
            ts = datetime.now(timezone.utc).isoformat()
            node = SessionNode(
                id=node.id,
                parent_id=node.parent_id,
                type=node.type,
                role=node.role,
                content=node.content,
                tool_calls=node.tool_calls,
                tool_call_id=node.tool_call_id,
                timestamp=ts,
            )

        line = json.dumps(node.to_dict(), ensure_ascii=False) + "\n"
        with cls.locked_file(p, "a") as f:
            f.write(line)
            f.flush()

        return node

    @classmethod
    def load_entries(cls, journal_path: str | Path) -> list[SessionNode]:
        """Read all session entries from an append-only JSONL journal."""
        p = Path(journal_path)
        if not p.exists():
            return []

        entries: list[SessionNode] = []
        with cls.locked_file(p, "r") as f:
            for line_idx, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    node = _parse_entry_to_node(data)
                    entries.append(node)
                except Exception as exc:
                    logger.warning(
                        "corrupt_journal_line_skipped",
                        line_idx=line_idx,
                        journal=str(p),
                        error=str(exc),
                    )
        return entries


__all__ = [
    "SessionJournalManager",
]
