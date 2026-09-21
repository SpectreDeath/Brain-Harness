"""AI-Native Harness Plugin — 4-Gate Behavioral Pipeline, Credential-Free MCP Security, and Drift Telemetry."""

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

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "ai-native-harness-engineer" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from ai_native_harness import AiNativeHarnessEngine

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.ai_native_harness import (
    AI_NATIVE_HARNESS_SERVICE_KEY,
    AiNativeHarnessAuditReportData,
    AiNativeHarnessService,
    FourGatesEvaluationData,
    HarnessDocDriftReportData,
    McpSecurityCheckData,
    NegativeBacklogReportData,
)

logger = structlog.get_logger(__name__)


class AiNativeHarnessPlugin(HarnessPlugin, AiNativeHarnessService):
    """Plugin providing in-memory 4-gate verification, drift calculus, MCP security, and demand mining."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = AiNativeHarnessEngine(root_dir=self._root)

    @property
    def name(self) -> str:
        return "plugin.ai_native_harness"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "4-gate behavioral pipeline verification, credential-free MCP security audit, "
            "code-to-doc drift calculus, and negative query demand mining"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AI_NATIVE_HARNESS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the AiNativeHarnessService into the IoC container."""
        context.provide(AI_NATIVE_HARNESS_SERVICE_KEY, self)
        logger.info(
            "ai_native_harness_service_provided",
            service=str(AI_NATIVE_HARNESS_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- AiNativeHarnessService Implementation ---

    def evaluate_gates(
        self,
        workspace_root: str | Path | None = None,
        config: dict[str, Any] | None = None,
    ) -> FourGatesEvaluationData:
        """Execute and score the 4 Behavioral Verification Gates."""
        gate_eval = self._engine.evaluate_gates(workspace_root=workspace_root, config=config)
        return FourGatesEvaluationData.model_validate(gate_eval.to_dict())

    def calculate_code_to_doc_drift(
        self,
        workspace_root: str | Path | None = None,
        mappings: list[dict[str, Any]] | None = None,
    ) -> HarnessDocDriftReportData:
        """Calculate Git code-to-doc commit drift across tracked assets."""
        drift_rep = self._engine.calculate_code_to_doc_drift(
            workspace_root=workspace_root, mappings=mappings
        )
        return HarnessDocDriftReportData.model_validate(drift_rep.to_dict())

    def audit_mcp_security(
        self,
        mcp_config_or_path: dict[str, Any] | str | Path | None = None,
    ) -> McpSecurityCheckData:
        """Audit MCP server configuration and endpoints for zero credentials and leak defense."""
        mcp_chk = self._engine.audit_mcp_security(mcp_config_or_path=mcp_config_or_path)
        return McpSecurityCheckData.model_validate(mcp_chk.to_dict())

    def mine_negative_backlog(
        self,
        queries: list[str] | None = None,
        logs_path: str | Path | None = None,
    ) -> NegativeBacklogReportData:
        """Cluster and rank unanswered assistant queries into prioritized documentation demand."""
        backlog_rep = self._engine.mine_negative_backlog(queries=queries, logs_path=logs_path)
        return NegativeBacklogReportData.model_validate(backlog_rep.to_dict())

    def audit(
        self,
        workspace_root: str | Path | None = None,
    ) -> AiNativeHarnessAuditReportData:
        """Execute full composite audit across all 3 pillars."""
        audit_rep = self._engine.audit(workspace_root=workspace_root)
        return AiNativeHarnessAuditReportData.model_validate(audit_rep.to_dict())

    def visual_brief(
        self,
        audit_report: Any | None = None,
        workspace_root: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and telemetry tables."""
        raw_report = None
        if audit_report is not None and hasattr(audit_report, "model_dump"):
            pass  # Pass down or let engine handle
        return self._engine.visual_brief(
            audit_report=raw_report,
            workspace_root=workspace_root,
            output_path=output_path,
        )


# Rule 45: Export module singleton plugin instance
plugin = AiNativeHarnessPlugin()


# Top-level entrypoints matching plugin.json tool declarations
def four_gates_evaluate(
    target: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for four_gates_evaluate tool invocation."""
    report = plugin.evaluate_gates(workspace_root=target)
    return report.model_dump()


def doc_drift_audit(
    target: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for doc_drift_audit tool invocation."""
    report = plugin.calculate_code_to_doc_drift(workspace_root=target)
    return report.model_dump()


def mcp_security_audit(
    config_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for mcp_security_audit tool invocation."""
    check = plugin.audit_mcp_security(mcp_config_or_path=config_path)
    return check.model_dump()


def negative_backlog_mine(
    logs_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for negative_backlog_mine tool invocation."""
    backlog = plugin.mine_negative_backlog(logs_path=logs_path)
    return backlog.model_dump()


def ai_native_harness_brief(
    target: str | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Top-level entrypoint for ai_native_harness_brief tool invocation."""
    brief_path = plugin.visual_brief(workspace_root=target, output_path=output_path)
    return str(brief_path)
