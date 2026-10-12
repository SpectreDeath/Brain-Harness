"""Layer 4 regression suite and Layer 5 statistical gating Click commands."""

from __future__ import annotations

import json as _json
from pathlib import Path

import click

from harness.commands.self_eval.resolver import get_self_eval_service


@click.command("regression")
@click.option(
    "--golden", "golden_path", required=True, help="Path to golden dataset JSON"
)
@click.option("--min-score", type=float, default=3.5, help="Minimum passing score")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def regression_cmd(golden_path: str, min_score: float, json_output: bool) -> None:
    """Execute CI/CD regression suite across curated golden test dataset."""
    svc = get_self_eval_service()
    rep = svc.run_golden_regression(
        golden_dataset_path=golden_path, min_judge_score=min_score
    )

    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    click.echo(f"Regression Suite Run: {rep.run_id}")
    click.echo(
        f"  Total Cases: {rep.total_cases} | Passed: {rep.passed_cases} ({rep.pass_rate * 100:.1f}%)"
    )
    click.echo(f"  Layer 1 Pass Rate: {rep.layer1_pass_rate * 100:.1f}%")
    click.echo(f"  Mean Score: {rep.mean_score:.2f} / 5.0")
    if rep.failures:
        click.echo(f"  Recorded Failures: {len(rep.failures)}")


@click.command("gate")
@click.option(
    "--before",
    "before_path",
    required=True,
    help="Path or JSON string of pre-change scores",
)
@click.option(
    "--after",
    "after_path",
    required=True,
    help="Path or JSON string of post-change scores",
)
@click.option(
    "--alpha", type=float, default=0.05, help="Statistical significance alpha"
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def gate_cmd(
    before_path: str,
    after_path: str,
    alpha: float,
    json_output: bool,
) -> None:
    """Run Stage 5 paired Student's t-test statistical significance deployment gate."""
    svc = get_self_eval_service()
    sb = (
        _json.loads(Path(before_path).read_text(encoding="utf-8"))
        if Path(before_path).exists()
        else _json.loads(before_path)
    )
    sa = (
        _json.loads(Path(after_path).read_text(encoding="utf-8"))
        if Path(after_path).exists()
        else _json.loads(after_path)
    )

    gate = svc.evaluate_statistical_significance_gate(sb, sa, alpha=alpha)
    if json_output:
        click.echo(_json.dumps(gate.model_dump(), indent=2))
        return

    badge = click.style(
        gate.decision, fg="green" if gate.decision == "APPROVED" else "red", bold=True
    )
    click.echo(f"Deployment Gate Verdict: {badge}")
    click.echo(f"  p-value: {gate.p_value:.4f} (alpha: {alpha})")
    click.echo(f"  Student's t-statistic: {gate.t_statistic:.3f}")
    click.echo(f"  Mean Score Delta: {gate.mean_difference:+.3f}")
    click.echo(f"  Justification: {gate.justification}")
