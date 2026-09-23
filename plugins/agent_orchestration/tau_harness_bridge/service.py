"""Concrete implementation of TauBridgeService protocol.

Elevates Pi-style coding agent harness capabilities (session trees, in-flight history repair,
project trust gating, JSON-RPC envelopes, append-only file-locked journaling) into the Harness IoC container.
Rule 45 & Rule 49: Authoritative in-memory IoC service provider.
"""

from __future__ import annotations

from harness.services.tau_bridge import (
    DefaultTauHarnessBridgeService,
    HistoryRepairReport,
    ProjectTrustEvaluation,
    RpcProtocolEnvelope,
    SessionPathResult,
    TauBridgeService,
)

__all__ = [
    "DefaultTauHarnessBridgeService",
    "HistoryRepairReport",
    "ProjectTrustEvaluation",
    "RpcProtocolEnvelope",
    "SessionPathResult",
    "TauBridgeService",
]
