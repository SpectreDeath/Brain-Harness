"""Proactor-safe SQLite database inspection and corpus scanning (Rule 22, Rule 32, Rule 52)."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from .constants import STEP_TYPE_MAP
from .models import ConversationManifest

logger = logging.getLogger("harness.services.conversation_trajectory_miner")


def connect_ro(db_path: Path | str) -> sqlite3.Connection:
    """Establish proactor-safe read-only SQLite URI connection (Rule 22)."""
    resolved = Path(db_path).resolve()
    uri_path = resolved.as_posix()
    uri = f"file:{uri_path}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=5.0)


def categorize_error(err_str: str, task_str: str) -> str:
    """Classify error string into semantic diagnostic categories."""
    combined = f"{err_str} {task_str}".lower()
    if "filenotfound" in combined or "no such file" in combined:
        return "FileNotFoundError / Path Missing"
    if "syntaxerror" in combined or "parse error" in combined or "indentation" in combined:
        return "SyntaxError / Script Parse"
    if "permission denied" in combined or "access is denied" in combined:
        return "PermissionDenied / Security Boundary"
    if "timeout" in combined or "deadlock" in combined:
        return "SubprocessTimeout / Resource Lock"
    if "validation" in combined or "schema" in combined:
        return "Schema / Validation Failure"
    if "connection" in combined or "socket" in combined:
        return "Network / Connection Failure"
    return "ToolExecution / General Error"


def inspect_conversation(db_path: Path) -> ConversationManifest | None:
    """Inspect a single conversation database and extract metadata safely."""
    cid = db_path.stem
    try:
        file_size = db_path.stat().st_size
    except OSError:
        return None

    has_wal = db_path.with_name(f"{db_path.name}-wal").exists()

    conn: sqlite3.Connection | None = None
    try:
        conn = connect_ro(db_path)
        cursor = conn.cursor()

        # Verify schema presence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps'")
        if not cursor.fetchone():
            return ConversationManifest(
                cid=cid,
                db_path=str(db_path),
                file_size_bytes=file_size,
                step_count=0,
                has_wal=has_wal,
                step_types={},
            )

        cursor.execute("SELECT COUNT(*) FROM steps")
        total_steps = cursor.fetchone()[0]

        cursor.execute("SELECT step_type, COUNT(*) FROM steps GROUP BY step_type")
        raw_step_types = dict(cursor.fetchall())
        mapped_step_types = {
            STEP_TYPE_MAP.get(k, f"TYPE_{k}"): v
            for k, v in raw_step_types.items()
        }

        # Status in (6, 7) or non-empty error_details indicates error/friction
        cursor.execute(
            "SELECT COUNT(*) FROM steps WHERE status IN (6, 7) OR (error_details IS NOT NULL AND length(error_details) > 0)"
        )
        errors_detected = cursor.fetchone()[0]

        # Count consecutive retry cascades
        cursor.execute("SELECT idx, status, step_type, error_details FROM steps ORDER BY idx ASC")
        rows = cursor.fetchall()
        retry_count = 0
        prev_failed = False
        for r in rows:
            status = r[1]
            err = r[3]
            is_err = status in (6, 7) or bool(err and len(str(err).strip()) > 0)
            if is_err:
                if prev_failed:
                    retry_count += 1
                prev_failed = True
            else:
                prev_failed = False

        # Extract first user prompt snippet via lossy UTF-8 decode
        cursor.execute("SELECT step_payload FROM steps WHERE idx=0 OR step_type=5 LIMIT 1")
        first_snippet = ""
        row = cursor.fetchone()
        if row and row[0]:
            raw_bytes = row[0]
            decoded = (
                raw_bytes.decode("utf-8", errors="ignore")
                if isinstance(raw_bytes, bytes)
                else str(raw_bytes)
            )
            clean_match = re.findall(r"[a-zA-Z0-9_\-\.\:\/\s\?\!\,\'\"]{10,}", decoded)
            if clean_match:
                first_snippet = clean_match[0][:150].strip()

        return ConversationManifest(
            cid=cid,
            db_path=str(db_path),
            file_size_bytes=file_size,
            step_count=total_steps,
            has_wal=has_wal,
            step_types=mapped_step_types,
            errors_detected=errors_detected,
            first_prompt_snippet=first_snippet,
            retry_count=retry_count,
        )
    except (NameError, TypeError, AttributeError):
        raise
    except Exception as exc:
        logger.debug("Failed inspecting database %s: %s", db_path, exc)
        return None
    finally:
        if conn is not None:
            conn.close()


def scan_corpus(corpus_dir: Path | str, max_dbs: int | None = None) -> list[ConversationManifest]:
    """Scan corpus directory and compile manifests for SQLite conversation databases."""
    path = Path(corpus_dir)
    if not path.exists():
        return []

    # Enforce bounded traversal and prune noise (Rule 52)
    db_files = sorted(
        [p for p in path.glob("*.db") if not p.name.endswith(("-shm", "-wal"))],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if max_dbs:
        db_files = db_files[:max_dbs]

    manifests: list[ConversationManifest] = []
    for p in db_files:
        m = inspect_conversation(p)
        if m:
            manifests.append(m)
    return manifests


__all__ = [
    "categorize_error",
    "connect_ro",
    "inspect_conversation",
    "scan_corpus",
]
