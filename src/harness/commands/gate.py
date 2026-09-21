"""Gate commands — headless CLI and IoC service seams for AI-native harness governance.

Provides CLI inspection for 4 behavioral verification gates, credential-free MCP security,
code-to-doc drift calculus, negative query demand mining, and HTML visual briefs.
"""

from __future__ import annotations

import json as _json
import sys
import webbrowser
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
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


def get_ai_native_harness_service(
    context: ServiceContext | None = None,
) -> AiNativeHarnessService:
    """Resolve AiNativeHarnessService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(AI_NATIVE_HARNESS_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.ai_native_harness.main import (
            plugin as harness_plugin,
        )

        return harness_plugin
    except Exception as exc:
        logger.warning("ai_native_harness_plugin_fallback_failed", error=str(exc))
        # Direct fallback to AiNativeHarnessEngine
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "ai-native-harness-engineer"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from ai_native_harness import AiNativeHarnessEngine  # type: ignore

        class _EngineAdapter(AiNativeHarnessService):
            def __init__(self) -> None:
                self._eng = AiNativeHarnessEngine(root_dir=_ws_root)

            def evaluate_gates(
                self,
                workspace_root: str | Path | None = None,
                config: dict[str, Any] | None = None,
            ) -> FourGatesEvaluationData:
                res = self._eng.evaluate_gates(workspace_root=workspace_root, config=config)
                return FourGatesEvaluationData.model_validate(res.to_dict())

            def calculate_code_to_doc_drift(
                self,
                workspace_root: str | Path | None = None,
                mappings: list[dict[str, Any]] | None = None,
            ) -> HarnessDocDriftReportData:
                res = self._eng.calculate_code_to_doc_drift(
                    workspace_root=workspace_root, mappings=mappings
                )
                return HarnessDocDriftReportData.model_validate(res.to_dict())

            def audit_mcp_security(
                self,
                mcp_config_or_path: dict[str, Any] | str | Path | None = None,
            ) -> McpSecurityCheckData:
                res = self._eng.audit_mcp_security(mcp_config_or_path=mcp_config_or_path)
                return McpSecurityCheckData.model_validate(res.to_dict())

            def mine_negative_backlog(
                self,
                queries: list[str] | None = None,
                logs_path: str | Path | None = None,
            ) -> NegativeBacklogReportData:
                res = self._eng.mine_negative_backlog(queries=queries, logs_path=logs_path)
                return NegativeBacklogReportData.model_validate(res.to_dict())

            def audit(
                self,
                workspace_root: str | Path | None = None,
            ) -> AiNativeHarnessAuditReportData:
                res = self._eng.audit(workspace_root=workspace_root)
                return AiNativeHarnessAuditReportData.model_validate(res.to_dict())

            def visual_brief(
                self,
                audit_report: Any | None = None,
                workspace_root: str | Path | None = None,
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.visual_brief(
                    audit_report=audit_report,
                    workspace_root=workspace_root,
                    output_path=output_path,
                )

        return _EngineAdapter()


@click.group("gate")
def gate_group() -> None:
    """AI-native harness governance, 4 behavioral gates, and drift telemetry."""


@gate_group.command("audit")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to audit (defaults to workspace root)",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output report as structured JSON",
)
def gate_audit_cli(
    target: str | None,
    as_json: bool,
) -> None:
    """Run comprehensive AI-native harness governance audit across all 3 pillars."""
    service = get_ai_native_harness_service()
    report = service.audit(workspace_root=target)

    if as_json:
        click.echo(_json.dumps(report.model_dump(), indent=2))
        return

    ge = report.gates_evaluation
    dd = report.doc_drift_report
    mc = report.mcp_security_check
    nb = report.negative_backlog

    click.echo(click.style("=== AI-Native Harness Governance Audit ===", fg="cyan", bold=True))
    click.echo(f"Target: {report.target_path}")
    click.echo(
        f"4 Behavioral Gates: Score {round(ge.overall_score * 100, 1)}% "
        f"({'PASS' if ge.all_passed else 'ACTION NEEDED'})"
    )
    click.echo(f"  Gate 1 (Typecheck):  {'PASS' if ge.gate1_typecheck.passed else 'FAIL'}")
    click.echo(f"  Gate 2 (Coverage):   {'PASS' if ge.gate2_coverage.passed else 'FAIL'}")
    click.echo(f"  Gate 3 (Simulation): {'PASS' if ge.gate3_e2e_simulation.passed else 'FAIL'}")
    click.echo(f"  Gate 4 (Live Demo):  {'PASS' if ge.gate4_live_demo.passed else 'FAIL'}")
    click.echo(f"  Payload Omission:    {'PASS' if ge.payload_omission_audit.passed else 'FAIL'}")
    click.echo(
        f"Code-to-Doc Drift:   {dd.total_drift_count} commits ({dd.amber_count} amber, {dd.green_count} green)"
    )
    click.echo(
        f"MCP Security Bridge: {'PASSED' if mc.passed else 'FAILED'} (Zero Creds: {mc.zero_stored_credentials})"
    )
    click.echo(
        f"Negative Backlog:    {nb.total_clusters} clusters from {nb.total_unanswered_queries} queries"
    )
    click.echo(f"\nSummary:\n  {report.summary}")


@gate_group.command("evaluate")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to evaluate",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output evaluation as structured JSON",
)
def gate_evaluate_cli(
    target: str | None,
    as_json: bool,
) -> None:
    """Evaluate the 4 Behavioral Verification Gates."""
    service = get_ai_native_harness_service()
    eval_res = service.evaluate_gates(workspace_root=target)

    if as_json:
        click.echo(_json.dumps(eval_res.model_dump(), indent=2))
        return

    click.echo(click.style("=== 4 Behavioral Verification Gates ===", fg="cyan", bold=True))
    click.echo(
        f"Overall Score: {round(eval_res.overall_score * 100, 1)}% "
        f"({'PASS' if eval_res.all_passed else 'FAIL'})"
    )
    click.echo(f"Gate 1 [Typecheck]:  {'PASS' if eval_res.gate1_typecheck.passed else 'FAIL'} - {eval_res.gate1_typecheck.details}")
    click.echo(f"Gate 2 [Coverage]:   {'PASS' if eval_res.gate2_coverage.passed else 'FAIL'} - {eval_res.gate2_coverage.details}")
    click.echo(f"Gate 3 [Simulation]: {'PASS' if eval_res.gate3_e2e_simulation.passed else 'FAIL'} - {eval_res.gate3_e2e_simulation.details}")
    click.echo(f"Gate 4 [Live Demo]:  {'PASS' if eval_res.gate4_live_demo.passed else 'FAIL'} - {eval_res.gate4_live_demo.details}")
    click.echo(f"Payload Omission:    {'PASS' if eval_res.payload_omission_audit.passed else 'FAIL'}")


@gate_group.command("mcp")
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Optional path to MCP configuration",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output security check as structured JSON",
)
def gate_mcp_cli(
    config_path: str | None,
    as_json: bool,
) -> None:
    """Audit MCP server posture for zero credentials, PAT forwarding, and uniform leak defense."""
    service = get_ai_native_harness_service()
    check = service.audit_mcp_security(mcp_config_or_path=config_path)

    if as_json:
        click.echo(_json.dumps(check.model_dump(), indent=2))
        return

    click.echo(click.style("=== Credential-Free MCP Security Bridge ===", fg="yellow", bold=True))
    click.echo(f"Security Posture: {'PASSED' if check.passed else 'ACTION NEEDED'} (Score: {check.score:.2f})")
    click.echo(f"Zero Stored Credentials:   {'YES' if check.zero_stored_credentials else 'NO'}")
    click.echo(f"User PAT Forwarding:       {'YES' if check.forward_user_tokens else 'NO'}")
    click.echo(f"Dynamic RBAC Enabled:      {'YES' if check.dynamic_rbac_enabled else 'NO'}")
    click.echo(f"Sanitized 403 Forbidden:   {'YES' if check.sanitized_403_forbidden else 'NO'}")
    click.echo(f"Identical 404 Leak Defense:{'YES' if check.identical_404_leak_defense else 'NO'}")
    click.echo(f"SME Workflow Markers:      {'YES' if check.human_sme_workflow_markers else 'NO'}")


@gate_group.command("drift")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to audit (defaults to workspace root)",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output drift report as structured JSON",
)
def gate_drift_cli(
    target: str | None,
    as_json: bool,
) -> None:
    """Calculate Git code-to-doc commit drift count and status badges."""
    service = get_ai_native_harness_service()
    report = service.calculate_code_to_doc_drift(workspace_root=target)

    if as_json:
        click.echo(_json.dumps(report.model_dump(), indent=2))
        return

    click.echo(click.style("=== Code-to-Doc Drift Telemetry ===", fg="cyan", bold=True))
    click.echo(f"Total Drift Count: {report.total_drift_count} commits")
    click.echo(f"Synchronized (Green): {report.green_count} | Drifted (Amber): {report.amber_count}")
    for it in report.items:
        click.echo(
            f"  [{it.status_badge.upper()}] {it.doc_slug} ({it.doc_path}): {it.drift_count} commits behind code"
        )


@gate_group.command("mine")
@click.option(
    "--logs",
    "-l",
    "logs_path",
    default=None,
    help="Optional path to query logs file",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output mined backlog as structured JSON",
)
def gate_mine_cli(
    logs_path: str | None,
    as_json: bool,
) -> None:
    """Mine unanswered assistant queries into a demand-ranked documentation backlog."""
    service = get_ai_native_harness_service()
    backlog = service.mine_negative_backlog(logs_path=logs_path)

    if as_json:
        click.echo(_json.dumps(backlog.model_dump(), indent=2))
        return

    click.echo(click.style("=== Unanswered Query Demand Backlog ===", fg="magenta", bold=True))
    click.echo(f"Total Unanswered Queries: {backlog.total_unanswered_queries}")
    click.echo(f"Topic Clusters: {backlog.total_clusters}")
    for it in backlog.items:
        click.echo(
            f"  [{it.priority.upper()}] {it.query_cluster} (Demand: {it.demand_count}) -> Suggests: {it.suggested_doc_slug}"
        )


@gate_group.command("brief")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to audit (defaults to workspace root)",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    default=None,
    help="Path where generated HTML brief will be saved",
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=False,
    help="Open generated visual brief in default web browser",
)
def gate_brief_cli(
    target: str | None,
    output_path: str | None,
    open_browser: bool,
) -> None:
    """Render interactive HTML visual brief with Mermaid topology and telemetry tables."""
    service = get_ai_native_harness_service()
    path = service.visual_brief(workspace_root=target, output_path=output_path)
    click.echo(f"Visual brief generated at: {path}")

    if open_browser:
        webbrowser.open(f"file://{path.resolve()}")
