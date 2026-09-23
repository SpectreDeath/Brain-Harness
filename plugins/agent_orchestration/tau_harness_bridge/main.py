"""TauHarnessBridge Plugin — Pi-Style Minimalist Coding Agent Harness Bridge.

Synthesized from Tau (huggingface/tau v0.4.4) and Pi architecture.
Provides in-memory micro-kernel IoC service implementation (Rule 45 & Rule 49).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"

if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.tau_bridge import (
    TAU_HARNESS_BRIDGE_SERVICE_KEY,
    DefaultTauHarnessBridgeService,
    HistoryRepairReport,
    ProjectTrustEvaluation,
    RpcProtocolEnvelope,
    SessionNode,
    SessionPathResult,
    TauBridgeService,
)

logger = structlog.get_logger(__name__)


class TauHarnessBridgePlugin(HarnessPlugin, TauBridgeService):
    """Plugin providing Pi-style coding agent harness operations."""

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultTauHarnessBridgeService()

    @property
    def name(self) -> str:
        return "plugin.tau_harness_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Pi-style minimalist coding agent harness bridge providing branchable session tree DAGs, "
            "locked append-only JSONL storage, provider-safe in-flight tool history repair, and project-trust security gating"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [TAU_HARNESS_BRIDGE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container (Rule 45)."""
        context.provide(TAU_HARNESS_BRIDGE_SERVICE_KEY, self)
        logger.info(
            "tau_harness_bridge_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Clean up resources on unload."""
        logger.info("tau_harness_bridge_plugin_unloaded")

    def resolve_session_path(
        self, entries: list[dict[str, Any]], target_entry_id: str
    ) -> SessionPathResult:
        """Resolve linear conversation ancestry from root to a target branch entry."""
        return self._service.resolve_session_path(entries, target_entry_id)

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairReport:
        """Normalize message history to guarantee provider tool-call and tool-result parity."""
        return self._service.repair_tool_history(messages)

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> ProjectTrustEvaluation:
        """Evaluate workspace trust boundaries, git root inheritance, and protected resources."""
        return self._service.evaluate_project_trust(project_path, trusted_roots)

    def format_rpc_envelope(
        self,
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> RpcProtocolEnvelope:
        """Format a Pi-compatible JSONL RPC message envelope."""
        return self._service.format_rpc_envelope(request_id, result=result, error=error)

    def append_journal_entry(
        self, journal_path: str | Path, entry: dict[str, Any] | SessionNode
    ) -> dict[str, Any]:
        """Atomically append a session node to an advisory locked JSONL journal."""
        return self._service.append_journal_entry(journal_path, entry)

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[dict[str, Any]]:
        """Load session entries from an append-only JSONL journal."""
        return self._service.load_journal_entries(journal_path)

    def render_session_tree(
        self, entries: list[dict[str, Any]], root_id: str | None = None
    ) -> str:
        """Render deterministic ASCII DAG tree representation."""
        return self._service.render_session_tree(entries, root_id=root_id)

    def find_branch_leaves(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find active branch tips / leaf nodes in a session tree."""
        return self._service.find_branch_leaves(entries)

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        return self._service.is_path_confined(target_path, root_path)


# Module-level singleton provider required by Rule 45
plugin = TauHarnessBridgePlugin()
