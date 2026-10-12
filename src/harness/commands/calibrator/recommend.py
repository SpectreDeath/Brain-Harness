"""Calibrator recommendation Click command."""

from __future__ import annotations

import json as _json

import click

from harness.commands.calibrator.resolver import get_calibrator_service


@click.command("recommend")
@click.option(
    "--model",
    "-m",
    "model_name",
    default="Claude-3.7-Sonnet",
    help="Target model identifier",
)
@click.option(
    "--params",
    "-p",
    "parameter_billions",
    type=float,
    default=550.0,
    help="Model parameter size in billions (e.g. 30, 120, 550)",
)
@click.option(
    "--workload",
    "-w",
    default="codebase_repo",
    help="Workload type: terminal_cli | codebase_repo | mixed",
)
@click.option(
    "--budget",
    "-b",
    "context_budget",
    type=int,
    default=131072,
    help="Context window usable budget in tokens",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output recommendation as structured JSON",
)
def calibrator_recommend_cli(
    model_name: str,
    parameter_billions: float,
    workload: str,
    context_budget: int,
    as_json: bool,
) -> None:
    """Derive optimal empirical harness configuration across model tiers and workloads."""
    service = get_calibrator_service()
    rec = service.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
        context_budget=context_budget,
    )

    if as_json:
        click.echo(_json.dumps(rec.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Coding Harness Calibration Recommendation ===", fg="cyan", bold=True
        )
    )
    click.echo(f"Model: {rec.model_name} ({parameter_billions}B parameters)")
    click.echo(f"Workload: {workload}")
    click.echo(
        f"Harness Operational Mode: "
        f"{click.style(rec.harness_mode.upper(), fg='green', bold=True)}"
    )
    click.echo(
        f"Action Space Interface: {click.style(rec.action_space, fg='yellow', bold=True)}"
    )
    click.echo(f"Context Staging Tier: {rec.context_tier} (Two-Tier Staging B1/B2)")
    click.echo(f"Planning Role: {rec.planning_role}")
    click.echo(
        f"Context Budget: {rec.budget_config.usable_window:,} tokens "
        f"(B1: {rec.budget_config.b1_tokens:,} / B2: {rec.budget_config.b2_tokens:,})"
    )
    click.echo(
        f"Stuck Detector: streak {rec.stuck_warn_threshold} warn / streak {rec.stuck_kill_threshold} kill"
    )
    if rec.deprecation_flags:
        click.echo(
            click.style(
                f"Pruned Machinery: {', '.join(rec.deprecation_flags)}", fg="magenta"
            )
        )
