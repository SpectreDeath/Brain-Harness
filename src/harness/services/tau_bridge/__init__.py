"""TauBridge service package facade.

Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
Rule 21: In-flight tool-call stream normalization & promotion.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
Rule 49: Authoritative in-memory domain engine for micro-kernel IoC elevation.
Rule 58: Single-seam resolver with standalone fallback.
"""

from __future__ import annotations

import sys

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.tau_bridge.engine import (
    PiHarnessEngine,
)
from harness.services.tau_bridge.journal import (
    SessionJournalManager,
)
from harness.services.tau_bridge.models import (
    BranchPath,
    HistoryRepairReport,
    HistoryRepairResult,
    JournalEntryRecord,
    ProjectTrustEvaluation,
    RpcProtocolEnvelope,
    SessionNode,
    SessionPathResult,
    ToolCallRecord,
    TrustScope,
)
from harness.services.tau_bridge.repair import (
    ToolHistoryRepairEngine,
)
from harness.services.tau_bridge.service import (
    TAU_BRIDGE_SERVICE_KEY,
    TAU_HARNESS_BRIDGE_SERVICE_KEY,
    DefaultTauHarnessBridgeService,
    TauBridgeService,
    resolve_tau_bridge,
)
from harness.services.tau_bridge.tree import (
    SessionTreeResolver,
)
from harness.services.tau_bridge.trust import (
    ProjectTrustEvaluator,
)

__all__ = [
    "BranchPath",
    "DefaultTauHarnessBridgeService",
    "HistoryRepairReport",
    "HistoryRepairResult",
    "JournalEntryRecord",
    "PiHarnessEngine",
    "ProjectTrustEvaluation",
    "ProjectTrustEvaluator",
    "RpcProtocolEnvelope",
    "SessionJournalManager",
    "SessionNode",
    "SessionPathResult",
    "SessionTreeResolver",
    "TAU_BRIDGE_SERVICE_KEY",
    "TAU_HARNESS_BRIDGE_SERVICE_KEY",
    "TauBridgeService",
    "ToolCallRecord",
    "ToolHistoryRepairEngine",
    "TrustScope",
    "resolve_tau_bridge",
]
