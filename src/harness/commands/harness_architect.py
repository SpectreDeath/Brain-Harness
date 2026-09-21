"""Harness Architect commands — headless CLI and IoC service seams for agent harness evaluation.

Provides CLI inspection for 5-part harness audits, 4-mechanism reliability scoring,
4-layer stack boundary audits, architectural bet classification, and HTML visual briefs.
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
from harness.services.agent_harness import (
    AGENT_HARNESS_ARCHITECT_SERVICE_KEY,
    AgentHarnessArchitectService,
    ArchitecturalBetRecommendationData,
    FourMechanismReliabilityGateData,
    HarnessAuditReportData,
)

logger = structlog.get_logger(__name__)


def get_harness_service(
    context: ServiceContext | None = None,
) -> AgentHarnessArchitectService:
    """Resolve AgentHarnessArchitectService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(AGENT_HARNESS_ARCHITECT_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.agent_harness_architect.main import (
            plugin as architect_plugin,
        )

        return architect_plugin
    except Exception as exc:
        logger.warning("agent_harness_architect_plugin_fallback_failed", error=str(exc))
        # Direct fallback to AgentHarnessArchitectEngine
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "agent-harness-architect"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from agent_harness_architect import AgentHarnessArchitectEngine  # type: ignore

        class _EngineAdapter(AgentHarnessArchitectService):
            def __init__(self) -> None:
                self._eng = AgentHarnessArchitectEngine(root_dir=_ws_root)

            def audit(
                self, target_path: str | Path | None = None
            ) -> HarnessAuditReportData:
                rep = self._eng.audit(target_path=target_path)
                return HarnessAuditReportData.model_validate(rep.to_dict())

            def evaluate_reliability(
                self, config_or_path: dict[str, Any] | str | Path | None = None
            ) -> FourMechanismReliabilityGateData:
                gate = self._eng.evaluate_reliability(config_or_path=config_or_path)
                return FourMechanismReliabilityGateData.model_validate(gate.to_dict())

            def classify_bet(
                self,
                bottleneck: str | None = None,
                requirements: list[str] | None = None,
            ) -> ArchitecturalBetRecommendationData:
                bet = self._eng.classify_bet(
                    bottleneck=bottleneck, requirements=requirements
                )
                return ArchitecturalBetRecommendationData.model_validate(bet.to_dict())

            def visual_brief(
                self,
                audit_report: Any | None = None,
                target_path: str | Path | None = None,
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.visual_brief(
                    audit_report=audit_report,
                    target_path=target_path,
                    output_path=output_path,
                )

        return _EngineAdapter()


@click.group("architect")
def architect_group() -> None:
    """Agent harness architecture audit, reliability scoring, and bet classification."""


@architect_group.command("audit")
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
def architect_audit_cli(
    target: str | None,
    as_json: bool,
) -> None:
    """Run comprehensive 5-part architecture and 4-layer stack boundary audit."""
    service = get_harness_service()
    report = service.audit(target_path=target)

    if as_json:
        click.echo(_json.dumps(report.model_dump(), indent=2))
        return

    fp = report.five_part_audit
    rg = report.reliability_gate
    bet = report.bet_recommendation

    click.echo(click.style("=== Harness Architecture Audit ===", fg="cyan", bold=True))
    click.echo(f"Target: {report.target_path}")
    click.echo(
        f"5-Part Overall Score: {round(fp.overall_score * 100, 1)}% "
        f"({'PASS' if fp.passed else 'FAIL'})"
    )
    click.echo(
        f"Reliability Level: Level {rg.overall_level} "
        f"(Production Gate: {'PASSED' if rg.meets_l2_production_gate else 'NOT MET'})"
    )
    click.echo(
        f"Recommended Bet: {bet.recommended_bet.upper()} ({bet.archetype_name})"
    )
    click.echo(
        f"Triple Budget: {'Enforced' if report.triple_budget_enforced else 'Unenforced'}"
    )
    click.echo(f"\nSummary:\n  {report.summary}")


@architect_group.command("score")
@click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Path to harness configuration YAML/JSON",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output scorecard as structured JSON",
)
def architect_score_cli(
    config_path: str | None,
    as_json: bool,
) -> None:
    """Evaluate 4 reliability mechanisms across Level 0 to Level 2."""
    service = get_harness_service()
    gate = service.evaluate_reliability(config_or_path=config_path)

    if as_json:
        click.echo(_json.dumps(gate.model_dump(), indent=2))
        return

    click.echo(click.style("=== 4-Mechanism Reliability Scorecard ===", fg="cyan", bold=True))
    click.echo(f"Overall Minimum Level: Level {gate.overall_level}")
    click.echo(
        f"Meets Level 2 Production Gate: "
        f"{'YES' if gate.meets_l2_production_gate else 'NO'}\n"
    )

    for m in [gate.planning, gate.sandbox, gate.subagents, gate.compression, gate.observability]:
        color = "green" if m.level == 2 else ("yellow" if m.level == 1 else "red")
        click.echo(click.style(f"• {m.name} [Level {m.level}: {m.level_name}]", fg=color, bold=True))
        click.echo(f"  Rationale: {m.rationale}")
        click.echo(f"  L2 Gate Met: {'Yes' if m.passed_l2_gate else 'No'}")


@architect_group.command("bet")
@click.option(
    "--bottleneck",
    "-b",
    default="",
    help="Description of team operational bottleneck",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output classification as structured JSON",
)
def architect_bet_cli(
    bottleneck: str,
    as_json: bool,
) -> None:
    """Classify team operational bottleneck into one of four architectural bets."""
    service = get_harness_service()
    bet = service.classify_bet(bottleneck=bottleneck)

    if as_json:
        click.echo(_json.dumps(bet.model_dump(), indent=2))
        return

    click.echo(click.style("=== Architectural Bet Matching ===", fg="cyan", bold=True))
    click.echo(f"Recommended Bet: {bet.recommended_bet.upper()}")
    click.echo(f"Archetype: {bet.archetype_name}")
    click.echo(f"Rationale: {bet.rationale}")
    if bet.tradeoffs:
        click.echo("\nAccepted Tradeoffs:")
        for t in bet.tradeoffs:
            click.echo(f"  - {t}")


@architect_group.command("brief")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to audit (defaults to workspace root)",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Destination file path for generated HTML brief",
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=False,
    help="Open generated HTML brief in default browser",
)
def architect_brief_cli(
    target: str | None,
    output: str | None,
    open_browser: bool,
) -> None:
    """Generate interactive HTML visual brief with Mermaid topology and reliability scorecard."""
    service = get_harness_service()
    out_path = service.visual_brief(target_path=target, output_path=output)
    click.echo(f"HTML visual brief generated at:\n  {out_path}")

    if open_browser:
        webbrowser.open(out_path.as_uri())
