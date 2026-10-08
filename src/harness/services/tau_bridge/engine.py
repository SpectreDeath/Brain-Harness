"""Unified PiHarnessEngine coordinator for coding agent harness mechanics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.tau_bridge.journal import SessionJournalManager
from harness.services.tau_bridge.models import (
    BranchPath,
    HistoryRepairResult,
    SessionNode,
    TrustScope,
)
from harness.services.tau_bridge.repair import ToolHistoryRepairEngine
from harness.services.tau_bridge.tree import SessionTreeResolver
from harness.services.tau_bridge.trust import ProjectTrustEvaluator


class PiHarnessEngine:
    """Unified coordinator for Pi-style coding agent harness operations."""

    def __init__(self) -> None:
        self.tree_resolver = SessionTreeResolver()
        self.history_repair = ToolHistoryRepairEngine()
        self.trust_evaluator = ProjectTrustEvaluator()
        self.journal_manager = SessionJournalManager()

    def resolve_session_path(
        self, entries: list[dict[str, Any] | SessionNode], target_id: str
    ) -> BranchPath:
        return self.tree_resolver.resolve_path(entries, target_id)

    def find_branch_leaves(
        self, entries: list[dict[str, Any] | SessionNode]
    ) -> list[SessionNode]:
        return self.tree_resolver.find_leaves(entries)

    def find_fork_points(
        self, entries: list[dict[str, Any] | SessionNode]
    ) -> dict[str, list[str]]:
        return self.tree_resolver.find_fork_points(entries)

    def render_session_tree(
        self,
        entries: list[dict[str, Any] | SessionNode],
        root_id: str | None = None,
    ) -> str:
        return self.tree_resolver.render_ascii_tree(entries, root_id=root_id)

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairResult:
        return self.history_repair.repair(messages)

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> TrustScope:
        return self.trust_evaluator.evaluate(project_path, trusted_roots)

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        return self.trust_evaluator.is_path_confined(target_path, root_path)

    def append_journal_entry(
        self, journal_path: str | Path, entry: SessionNode | dict[str, Any]
    ) -> SessionNode:
        return self.journal_manager.append_entry(journal_path, entry)

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[SessionNode]:
        return self.journal_manager.load_entries(journal_path)

    @staticmethod
    def format_rpc_envelope(
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format Pi-compatible JSON-RPC envelope."""
        env: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error is not None:
            env["error"] = error
        else:
            env["result"] = result
        return env


__all__ = [
    "PiHarnessEngine",
]
