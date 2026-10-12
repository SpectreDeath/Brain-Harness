"""Layer 2 anchored semantic judging Click command."""

from __future__ import annotations

import json as _json

import click

from harness.commands.self_eval.resolver import get_self_eval_service


@click.command("judge")
@click.argument("prompt")
@click.argument("response")
@click.option("--model", default="gpt-4o-mini", help="Judge model identifier")
@click.option("--judges", type=int, default=3, help="Number of consensus judges")
@click.option("--threshold", type=float, default=3.5, help="Minimum passing score")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def judge_cmd(
    prompt: str,
    response: str,
    model: str,
    judges: int,
    threshold: float,
    json_output: bool,
) -> None:
    """Execute Layer 2 anchored semantic evaluation with median consensus."""
    svc = get_self_eval_service()
    res = svc.evaluate_layer2_judge(
        prompt=prompt,
        response=response,
        model=model,
        num_judges=judges,
        threshold=threshold,
    )

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    status_icon = "PASS" if res.passed else "FAIL"
    click.echo(
        f"Layer 2 Judge Status: {status_icon} (Median Score: {res.median_score:.1f} / 5.0, Mean: {res.mean_score:.2f})"
    )
    click.echo(f"  Individual Scores: {res.scores}")
    for j in res.judge_results:
        click.echo(f"  - [{j['judge_id']}] Score: {j['score']} | {j['reasoning']}")
