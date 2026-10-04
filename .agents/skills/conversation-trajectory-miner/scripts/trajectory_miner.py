#!/usr/bin/env python3
"""Conversation Trajectory Miner Engine — Thin CLI Wrapper & Adapter (Rule 49).

Delegates domain logic to the micro-kernel service implementation in
harness.services.conversation_trajectory_miner while providing backward-compatible CLI
and module interface seams.

Enforces:
- Rule 12: Slotted & frozen dataclasses
- Rule 22: Multi-store memory federation & read-only SQLite URI mode (file:...?mode=ro)
- Rule 23, Rule 50: Windows UTF-8 codec and sys.path entrypoint invariant
- Rule 32: Defensive batch exception logging (never bare except: continue)
- Rule 33: JSON null-field fallback (dict.get("key") or [])
- Rule 40: Canonical Knowledge Vault dual-file format (metadata.json + summary.md)
- Rule 41: Dual-lens cognitive distillation with unbroken isnad claims
- Rule 48: Large corpus binary byte-offset seek invariant
- Rule 49: Skill-to-IoC micro-kernel seam elevation
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Windows UTF-8 stream codec & sys.path precedence invariant (Rule 23, 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(WORKSPACE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "src"))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from harness.services.conversation_trajectory_miner import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    STATUS_MAP,
    STEP_TYPE_MAP,
    CognitiveBifurcationReport,
    ConversationManifest,
    ConversationTrajectoryMinerService,
    FailureCluster,
    FrictionScorecard,
    IsnadClaimRecord,
    StandardConversationTrajectoryMinerService,
    TrajectoryStepRecord,
)

logger = logging.getLogger("trajectory_miner")

# Default service engine instance for standalone execution
_default_service = StandardConversationTrajectoryMinerService()

# Backward-compatibility alias
StepRecord = TrajectoryStepRecord


class ByteOffsetSeekTable:
    """O(1) binary byte-offset seek index for large transcript logs (Rule 48)."""

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)
        self.offsets: dict[int, tuple[int, int]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Scan file once in binary mode to record byte offset and length per line."""
        if not self.file_path.exists():
            return

        with open(self.file_path, "rb") as f:
            idx = 0
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                length = len(line)
                self.offsets[idx] = (offset, length)
                idx += 1

    def get_line(self, line_idx: int) -> str | None:
        """Fetch line by index in O(1) time without loading entire file."""
        if line_idx not in self.offsets:
            return None
        offset, length = self.offsets[line_idx]
        with open(self.file_path, "rb") as f:
            f.seek(offset)
            raw = f.read(length)
            return raw.decode("utf-8", errors="ignore")

    def total_lines(self) -> int:
        return len(self.offsets)


class ConversationTrajectoryMiner:
    """Backward-compatible adapter class delegating to StandardConversationTrajectoryMinerService."""

    def __init__(
        self,
        corpus_dir: Path | str,
        service: ConversationTrajectoryMinerService | None = None,
    ) -> None:
        self.corpus_dir = Path(corpus_dir)
        self.service = service or _default_service

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        return self.service.connect_ro(db_path)

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        return self.service.inspect_conversation(db_path)

    def scan_corpus(self, max_dbs: int | None = None) -> list[ConversationManifest]:
        return self.service.scan_corpus(self.corpus_dir, max_dbs=max_dbs)

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> dict[str, Any]:
        card = self.service.compile_friction_scorecard(manifests)
        return {
            "total_conversations": card.total_conversations,
            "total_steps": card.total_steps,
            "total_bytes_mb": card.total_bytes_mb,
            "total_errors": card.total_errors,
            "error_rate": card.error_rate,
            "step_type_distribution": card.step_type_distribution,
            "high_friction_sessions": list(card.high_friction_sessions),
        }


def main() -> None:
    """CLI entrypoint delegating to StandardConversationTrajectoryMinerService."""
    parser = argparse.ArgumentParser(
        description="Mine IDE conversation databases and execution logs."
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=os.environ.get(
            "HARNESS_CONVERSATIONS_DIR",
            r"C:\Users\spectre\.gemini\antigravity-ide\conversations",
        ),
        help="Path to conversations directory containing SQLite WAL databases.",
    )
    parser.add_argument(
        "--max-dbs",
        type=int,
        default=50,
        help="Maximum conversation databases to scan.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON diagnostic payload.",
    )

    args = parser.parse_args()
    service = StandardConversationTrajectoryMinerService()
    manifests = service.scan_corpus(args.corpus_dir, max_dbs=args.max_dbs)
    scorecard = service.compile_friction_scorecard(manifests)

    if args.json:
        payload = {
            "total_conversations": scorecard.total_conversations,
            "total_steps": scorecard.total_steps,
            "total_bytes_mb": scorecard.total_bytes_mb,
            "total_errors": scorecard.total_errors,
            "error_rate": scorecard.error_rate,
            "step_type_distribution": scorecard.step_type_distribution,
            "high_friction_sessions": list(scorecard.high_friction_sessions),
            "failure_clusters": [
                {
                    "error_type": fc.error_type,
                    "count": fc.count,
                    "sample_cids": list(fc.sample_cids),
                    "tool_names": list(fc.tool_names),
                    "sample_messages": list(fc.sample_messages),
                }
                for fc in scorecard.failure_clusters
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print("=== Conversation Trajectory Miner Scorecard ===")
        print(f"Corpus Path:         {args.corpus_dir}")
        print(f"Scanned DBs:         {scorecard.total_conversations}")
        print(f"Total Steps:         {scorecard.total_steps}")
        print(f"Total Size:          {scorecard.total_bytes_mb} MB")
        print(
            f"Total Errors:        {scorecard.total_errors} (rate: {scorecard.error_rate * 100:.2f}%)"
        )
        print(f"Step Types:          {scorecard.step_type_distribution}")
        print(f"High-Friction CIDs:  {len(scorecard.high_friction_sessions)}")
        if scorecard.failure_clusters:
            print("Top Failure Clusters:")
            for fc in scorecard.failure_clusters[:5]:
                print(f"  - {fc.error_type}: {fc.count} errors")


if __name__ == "__main__":
    main()
