"""Click CLI command group for PyRIT GenAI Red-Teaming (Rules 6, 10, 23)."""

from __future__ import annotations

import sys
import click

from harness.commands._utils import _run_async
from harness.services.pyrit_scanner import (
    AttackVector,
    DefaultPyritScannerService,
    RedTeamTarget,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@click.group("redteam")
def redteam_group() -> None:
    """GenAI adversarial red-teaming and prompt vulnerability audits."""
    pass


@redteam_group.command("scan")
@click.argument("prompt", required=True)
@click.option("--technique", default="crescendo", help="Attack technique (crescendo, roleplay_jailbreak, encoding_fuzz)")
@click.option("--intensity", default=3, type=int, help="Attack intensity from 1 to 5")
@click.option("--target-type", default="system_prompt", help="Target type (system_prompt, agent_loop, tool_interface)")
def scan_cmd(prompt: str, technique: str, intensity: int, target_type: str) -> None:
    """Run an adversarial probe scan against a target prompt or agent loop."""
    async def _run() -> None:
        svc = DefaultPyritScannerService()
        target = RedTeamTarget(target_type=target_type, endpoint="cli")
        vector = AttackVector(technique=technique, intensity=intensity)
        click.echo(f"Initiating adversarial scan [technique={technique}, intensity={intensity}]...")
        card = await svc.scan_target(target, vector)
        click.echo(f"Scorecard: Risk={card.risk_level.upper()} | Attack Success Rate={card.attack_success_rate * 100:.1f}%")
        if card.leaked_system_tokens:
            click.echo(f"  Leaked Tokens: {', '.join(card.leaked_system_tokens)}")
        if card.bypassed_tool_boundaries:
            click.echo(f"  Bypassed Boundaries: {', '.join(card.bypassed_tool_boundaries)}")
        if card.recommendations:
            click.echo("  Recommendations:")
            for rec in card.recommendations:
                click.echo(f"    - {rec}")

    _run_async(_run())


@redteam_group.command("techniques")
def techniques_cmd() -> None:
    """List all supported adversarial red-teaming techniques."""
    svc = DefaultPyritScannerService()
    techs = svc.list_available_techniques()
    click.echo(f"Supported adversarial techniques ({len(techs)}):")
    for t in techs:
        click.echo(f"  - {t}")


@redteam_group.command("status")
def status_cmd() -> None:
    """Show sandbox virtual environment status and isolation metrics."""
    svc = DefaultPyritScannerService()
    status = svc.get_runtime_status()
    click.echo("PyRIT Scanner Runtime Status:")
    for k, v in status.items():
        click.echo(f"  {k}: {v}")
