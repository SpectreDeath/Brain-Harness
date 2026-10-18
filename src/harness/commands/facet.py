"""Differential Facet Verifier CLI Commands.

Provides headless Click CLI inspection, comparison, absence claimability evaluation,
and differential report verification for multi-provider observation dossiers.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import click

from harness.services.differential_facet import (
    CoverageDeclaration,
    DifferentialReport,
    StandardDifferentialFacetService,
    canonicalize_json,
)


def _load_json_file(file_path: Path) -> dict[str, Any]:
    try:
        content = file_path.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception as exc:
        raise click.ClickException(f"Failed to load JSON file '{file_path}': {exc}")


@click.group("facet")
def facet_group() -> None:
    """Differential Facet Verifier — Multi-provider evidence comparison and facet availability semantics."""


@facet_group.command("compare")
@click.argument("left_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("right_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--provider-differ/--same-provider", default=None, help="Explicitly toggle cross-provider syntax decoupling")
@click.option("--format", "out_format", type=click.Choice(["rich", "plain", "json"]), default="rich", help="Output format")
def facet_compare_cmd(left_file: Path, right_file: Path, provider_differ: bool | None, out_format: str) -> None:
    """Compare two observation dossiers and emit a 3-valued DifferentialReport."""
    left_data = _load_json_file(left_file)
    right_data = _load_json_file(right_file)

    service = StandardDifferentialFacetService()
    kwargs = {}
    if provider_differ is not None:
        kwargs["providers_differ"] = provider_differ

    report = service.compare_observations(left_data, right_data, **kwargs)
    exported = service.export_report(report)

    if out_format == "json":
        click.echo(json.dumps(exported, indent=2, ensure_ascii=False))
        return

    if out_format == "plain":
        click.echo(f"Report ID: {report.report_id}")
        click.echo(f"Overall Status: {report.overall_status}")
        click.echo(f"Summary Digest: {report.summary_digest}")
        click.echo("Dimensions:")
        for dim in report.dimensions:
            click.echo(f"  - {dim.dimension:14s}: {dim.status:9s} [{dim.conclusion_kind}]")
            for limit in dim.limitations:
                click.echo(f"      * {limit}")
        return

    # Rich table output
    click.echo("=" * 72)
    click.echo(f" DIFFERENTIAL FACET VERIFIER REPORT: {report.report_id}")
    click.echo(f" Overall Status: {report.overall_status.upper()} | Digest: {report.summary_digest[:16]}...")
    click.echo("-" * 72)
    click.echo(f"{'Dimension':<16} | {'Status':<10} | {'Conclusion':<20} | {'Counts (L/R)'}")
    click.echo("-" * 72)
    for dim in report.dimensions:
        l_cnt = str(dim.left_count) if dim.left_count is not None else "null"
        r_cnt = str(dim.right_count) if dim.right_count is not None else "null"
        counts = f"{l_cnt} / {r_cnt}"
        click.echo(f"{dim.dimension:<16} | {dim.status:<10} | {dim.conclusion_kind:<20} | {counts}")
        for limit in dim.limitations:
            click.echo(f"  └─ limitation: {limit}")
    click.echo("=" * 72)


@facet_group.command("claim-absence")
@click.argument("coverage_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def facet_claim_absence_cmd(coverage_file: Path) -> None:
    """Evaluate whether an absence claim is legally valid under declared traversal coverage."""
    cov_data = _load_json_file(coverage_file)
    coverage = CoverageDeclaration(
        scope=cov_data.get("scope", "dossier"),
        status=cov_data.get("status", "unknown"),
        truncated=bool(cov_data.get("truncated", False)),
        omitted_count=int(cov_data.get("omitted_count", 0)),
    )
    service = StandardDifferentialFacetService()
    is_claimable = service.validate_absence_claim(coverage)

    result = {
        "absence_claimable": is_claimable,
        "scope": coverage.scope,
        "status": coverage.status,
        "truncated": coverage.truncated,
        "omitted_count": coverage.omitted_count,
    }
    if not is_claimable:
        reasons = []
        if coverage.status != "complete":
            reasons.append(f"status is '{coverage.status}' (must be 'complete')")
        if coverage.truncated:
            reasons.append("coverage was marked truncated")
        if coverage.omitted_count > 0:
            reasons.append(f"omitted_count is {coverage.omitted_count} (must be 0)")
        result["rejection_reasons"] = reasons

    click.echo(json.dumps(result, indent=2))


@facet_group.command("verify")
@click.argument("report_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--strict", is_flag=True, help="Exit non-zero if overall status is 'unknown'")
def facet_verify_cmd(report_file: Path, strict: bool) -> None:
    """Audit report integrity and verify absence claim validity."""
    rep_data = _load_json_file(report_file)
    rep_id = rep_data.get("report_id") or ""
    overall_status = rep_data.get("overall_status") or "unknown"
    dimensions = rep_data.get("dimensions") or []

    if not rep_id.startswith("rep:"):
        raise click.ClickException(f"Invalid report ID '{rep_id}': missing rep: prefix")

    unknown_dims = [d.get("dimension") for d in dimensions if d.get("status") == "unknown"]

    click.echo(f"Verified report integrity for {rep_id}: overall={overall_status}")
    if unknown_dims:
        click.echo(f"Warning: {len(unknown_dims)} dimension(s) carry 'unknown' status: {', '.join(unknown_dims)}")

    if strict and overall_status == "unknown":
        click.echo("Strict check failed: overall status is 'unknown'", err=True)
        sys.exit(1)


@facet_group.command("export")
@click.argument("report_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def facet_export_cmd(report_file: Path) -> None:
    """Export machine-parseable JSON certificate from a differential report."""
    rep_data = _load_json_file(report_file)
    click.echo(json.dumps(rep_data, indent=2, ensure_ascii=False))
