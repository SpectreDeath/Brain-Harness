#!/usr/bin/env python3
# /// script
# dependencies = ["click", "structlog", "pydantic"]
# ///
"""Pi-Style Minimalist Coding Agent Harness Engine & Skill Seam.

Delegates authoritatively to `harness.services.tau_bridge` (Rule 49).
Provides slotted & frozen domain models, DAG session tree ancestry resolution,
locked append-only JSONL journaling, in-flight provider-safe tool history repair,
and project-trust security gating.
Grounded in Tau (v0.4.4, huggingface/tau) and Pi architecture.

Rule 10: Headless CLI Introspection Seams.
Rule 12: Slotted & Frozen Dataclass Architecture.
Rule 21: In-Flight Tool-Call Stream Normalization & Promotion.
Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant.
Rule 45 & Rule 49: Skill-to-IoC Micro-Kernel Seam Elevation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Rule 23 & Rule 50: UTF-8 standard stream reconfigure and sys.path precedence
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Authoritative elevation from harness.services.tau_bridge (Rule 49)
from harness.services.tau_bridge import (
    BranchPath,
    HistoryRepairResult,
    JournalEntryRecord,
    PiHarnessEngine,
    ProjectTrustEvaluator,
    SessionJournalManager,
    SessionNode,
    SessionTreeResolver,
    ToolCallRecord,
    ToolHistoryRepairEngine,
    TrustScope,
)

__all__ = [
    "BranchPath",
    "HistoryRepairResult",
    "JournalEntryRecord",
    "PiHarnessEngine",
    "ProjectTrustEvaluator",
    "SessionJournalManager",
    "SessionNode",
    "SessionTreeResolver",
    "ToolCallRecord",
    "ToolHistoryRepairEngine",
    "TrustScope",
]

if __name__ == "__main__":
    engine = PiHarnessEngine()
    print("PiHarnessEngine initialized successfully via harness.services.tau_bridge.")
