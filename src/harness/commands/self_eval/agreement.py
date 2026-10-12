"""Layer 3 Cohen's Kappa agreement and judge drift audit Click commands."""

from __future__ import annotations

import json as _json
from pathlib import Path

import click

from harness.commands.self_eval.resolver import get_self_eval_service


@click.command("kappa")
@click.argument("annotations_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def kappa_cmd(annotations_file: str, json_output: bool) -> None:
    """Calculate Layer 3 Cohen's Kappa human inter-annotator agreement."""
    svc = get_self_eval_service()
    raw = _json.loads(Path(annotations_file).read_text(encoding="utf-8"))
    ann_a = raw.get("rater_a", [])
    ann_b = raw.get("rater_b", [])

    rep = svc.calculate_cohens_kappa(ann_a, ann_b)
    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    verdict = "ACCEPTABLE" if rep.is_acceptable else "UNACCEPTABLE (kappa <= 0.6)"
    click.echo(f"Cohen's Kappa: {rep.cohens_kappa:.3f} ({verdict})")
    click.echo(f"  Observed Agreement: {rep.observed_agreement * 100:.1f}%")
    click.echo(
        f"  Expected Chance Agreement: {rep.expected_chance_agreement * 100:.1f}%"
    )
    click.echo(f"  Paired Samples: {rep.paired_samples_count}")
    click.echo(f"  Interpretation: {rep.interpretation}")


@click.command("drift")
@click.option(
    "--human", "human_path", required=True, help="Path to JSON file of human scores"
)
@click.option(
    "--judge", "judge_path", required=True, help="Path to JSON file of judge scores"
)
@click.option("--max-drift", type=float, default=0.5, help="Maximum allowable drift")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def drift_cmd(
    human_path: str,
    judge_path: str,
    max_drift: float,
    json_output: bool,
) -> None:
    """Audit automated LLM judge drift against human calibration ratings."""
    svc = get_self_eval_service()
    h_scores = _json.loads(Path(human_path).read_text(encoding="utf-8"))
    j_scores = _json.loads(Path(judge_path).read_text(encoding="utf-8"))

    rep = svc.audit_judge_drift(h_scores, j_scores, max_allowed_drift=max_drift)
    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    verdict = "DRIFT DETECTED" if rep.drift_detected else "STABLE"
    click.echo(f"Judge Drift Audit: {verdict}")
    click.echo(
        f"  Mean Absolute Deviation: {rep.mean_absolute_deviation:.3f} (Max: {rep.max_allowed_drift:.2f})"
    )
    click.echo(f"  Benchmark Samples: {rep.sample_count}")
