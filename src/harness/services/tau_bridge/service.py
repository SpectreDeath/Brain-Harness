"""Typed Service Protocol, Default Implementation, and Single-Seam Resolver for tau_bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.tau_bridge.engine import PiHarnessEngine
from harness.services.tau_bridge.models import (
    HistoryRepairReport,
    ProjectTrustEvaluation,
    RpcProtocolEnvelope,
    SessionNode,
    SessionPathResult,
)


@runtime_checkable
class TauBridgeService(Protocol):
    """Protocol for Pi-style coding agent harness operations."""

    def resolve_session_path(
        self, entries: list[dict[str, Any]], target_entry_id: str
    ) -> SessionPathResult:
        """Resolve linear conversation ancestry from root to a target branch entry."""
        ...

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairReport:
        """Normalize message history to guarantee provider tool-call and tool-result parity."""
        ...

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> ProjectTrustEvaluation:
        """Evaluate workspace trust boundaries, git root inheritance, and protected resources."""
        ...

    def format_rpc_envelope(
        self,
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> RpcProtocolEnvelope:
        """Format a Pi-compatible JSONL RPC message envelope."""
        ...

    def append_journal_entry(
        self, journal_path: str | Path, entry: dict[str, Any] | SessionNode
    ) -> dict[str, Any]:
        """Atomically append a session node to an advisory locked JSONL journal."""
        ...

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[dict[str, Any]]:
        """Load session entries from an append-only JSONL journal."""
        ...

    def render_session_tree(
        self, entries: list[dict[str, Any]], root_id: str | None = None
    ) -> str:
        """Render deterministic ASCII DAG tree representation."""
        ...

    def find_branch_leaves(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find active branch tips / leaf nodes in a session tree."""
        ...

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        ...


class DefaultTauHarnessBridgeService(TauBridgeService):
    """Default authoritative implementation of TauBridgeService."""

    def __init__(self, engine: Any | None = None) -> None:
        self._engine = engine or PiHarnessEngine()

    def resolve_session_path(
        self, entries: list[dict[str, Any]], target_entry_id: str
    ) -> SessionPathResult:
        """Resolve linear conversation ancestry from root to a target branch entry."""
        res = self._engine.resolve_session_path(entries, target_entry_id)
        return SessionPathResult(
            target_id=res.target_id,
            path_entries=[node.to_dict() for node in res.path_entries],
            depth=res.depth,
            total_tree_entries=res.total_entries,
            branch_count=res.branch_count,
        )

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairReport:
        """Normalize message history to guarantee provider tool-call and tool-result parity."""
        res = self._engine.repair_tool_history(messages)
        return HistoryRepairReport(
            repaired_messages=list(res.repaired_messages),
            dropped_count=res.dropped_count,
            synthesized_count=res.synthesized_count,
            repairs_applied=list(res.repairs_applied),
            is_modified=res.is_modified,
        )

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> ProjectTrustEvaluation:
        """Evaluate workspace trust boundaries, git root inheritance, and protected resources."""
        res = self._engine.evaluate_project_trust(project_path, trusted_roots)
        return ProjectTrustEvaluation(
            project_path=res.project_path,
            is_trusted=res.is_trusted,
            git_root=res.git_root,
            protected_assets=list(res.protected_assets),
            warnings=list(res.warnings),
            permission_level=res.permission_level,
        )

    def format_rpc_envelope(
        self,
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> RpcProtocolEnvelope:
        """Format a Pi-compatible JSONL RPC message envelope."""
        env = self._engine.format_rpc_envelope(request_id, result=result, error=error)
        return RpcProtocolEnvelope(
            jsonrpc=env["jsonrpc"],
            id=env["id"],
            result=env.get("result"),
            error=env.get("error"),
        )

    def append_journal_entry(
        self, journal_path: str | Path, entry: dict[str, Any] | SessionNode
    ) -> dict[str, Any]:
        """Atomically append a session node to an advisory locked JSONL journal."""
        node = self._engine.append_journal_entry(journal_path, entry)
        return node.to_dict()

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[dict[str, Any]]:
        """Load session entries from an append-only JSONL journal."""
        nodes = self._engine.load_journal_entries(journal_path)
        return [node.to_dict() for node in nodes]

    def render_session_tree(
        self, entries: list[dict[str, Any]], root_id: str | None = None
    ) -> str:
        """Render deterministic ASCII DAG tree representation."""
        return self._engine.render_session_tree(entries, root_id=root_id)

    def find_branch_leaves(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find active branch tips / leaf nodes in a session tree."""
        nodes = self._engine.find_branch_leaves(entries)
        return [node.to_dict() for node in nodes]

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        return self._engine.is_path_confined(target_path, root_path)


TAU_HARNESS_BRIDGE_SERVICE_KEY: ServiceKey[TauBridgeService] = ServiceKey(
    "service.tau_harness_bridge"
)

# Backward-compatibility alias
TAU_BRIDGE_SERVICE_KEY = TAU_HARNESS_BRIDGE_SERVICE_KEY


def resolve_tau_bridge(
    context: ServiceContext | None = None,
) -> TauBridgeService:
    """Rule 58: Single-seam resolver with standalone fallback for TauBridgeService."""
    if context is not None:
        svc = context.optional(TAU_HARNESS_BRIDGE_SERVICE_KEY)
        if svc is not None and isinstance(svc, TauBridgeService):
            return svc

    return DefaultTauHarnessBridgeService()


__all__ = [
    "DefaultTauHarnessBridgeService",
    "TAU_BRIDGE_SERVICE_KEY",
    "TAU_HARNESS_BRIDGE_SERVICE_KEY",
    "TauBridgeService",
    "resolve_tau_bridge",
]
