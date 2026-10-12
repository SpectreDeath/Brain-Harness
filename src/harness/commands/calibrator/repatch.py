"""Fan et al. empirical re-patch forecasting Click command."""

from __future__ import annotations

import json as _json

import click

from harness.commands.calibrator.resolver import get_calibrator_service


@click.command("repatch")
@click.option(
    "--model-scale",
    "-m",
    default="strong_550b",
    help="Model scale: weak_30b | mid_120b | strong_550b",
)
@click.option(
    "--action-space",
    "-a",
    default="bash_only",
    help="Action space: predefined_tools | bash_only",
)
@click.option(
    "--workload",
    "-w",
    default="terminal_cli",
    help="Workload: terminal_cli | codebase_repo | mixed",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output prediction as structured JSON",
)
def calibrator_repatch_cli(
    model_scale: str,
    action_space: str,
    workload: str,
    as_json: bool,
) -> None:
    """Predict re-patch churn, action granularity, and cost reduction using Fan et al. empirical laws."""
    service = get_calibrator_service()
    pred = service.predict_repatch(
        model_capability=model_scale,
        action_space=action_space,
        workload=workload,
    )

    if as_json:
        click.echo(_json.dumps(pred.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Empirical Re-Patch & Cost Prediction (Fan et al.) ===",
            fg="cyan",
            bold=True,
        )
    )
    click.echo(f"Model Scale: {pred.model_scale}")
    click.echo(f"Workload: {pred.workload}")
    click.echo(f"Action Space: {pred.action_space}")
    click.echo(
        f"Predicted Mean Re-patches: "
        f"{click.style(str(pred.predicted_mean_repatches), fg='green' if pred.predicted_mean_repatches <= 2.0 else 'yellow', bold=True)}"
    )
    click.echo(f"Coarse Action Ratio: {int(pred.coarse_replace_ratio * 100)}%")
    click.echo(
        f"Estimated Cost Reduction: "
        f"{click.style(f'{pred.estimated_cost_reduction_pct}%', fg='green' if pred.estimated_cost_reduction_pct > 0 else 'red', bold=True)}"
    )
    click.echo(f"\nEmpirical Rationale:\n  {pred.rationale}")
