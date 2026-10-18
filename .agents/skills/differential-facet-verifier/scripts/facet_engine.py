# /// script
# dependencies = [
#   "click",
#   "structlog",
# ]
# ///
"""Differential Facet Verifier & Availability Semantics Engine.

Standalone execution script providing CLI evaluation for multi-provider dossiers,
absence claimability gates, and 3-valued differential outcome synthesis.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Rule 23 & Rule 50: Configure standard streams to UTF-8
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Rule 50: Prepend workspace root and src to sys.path
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_workspace_root / "src") not in sys.path:
    sys.path.insert(0, str(_workspace_root / "src"))
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

import click

from harness.services.differential_facet import (
    CoverageDeclaration,
    DifferentialReport,
    StandardDifferentialFacetService,
    canonicalize_json,
)


def _read_json(path_str: str) -> dict:
    p = Path(path_str)
    if not p.exists():
        raise click.ClickException(f"File not found: {path_str}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise click.ClickException(f"Failed to parse JSON in {path_str}: {exc}")


@click.group()
def cli() -> None:
    """Differential Facet Verifier & Availability Semantics Engine."""


@cli.command("compare")
@click.argument("left", type=click.Path(exists=True))
@click.argument("right", type=click.Path(exists=True))
@click.option("--providers-differ/--same-provider", default=None, help="Force cross-provider syntax decoupling")
@click.option("--format", "out_format", type=click.Choice(["rich", "plain", "json"]), default="rich")
def compare_cmd(left: str, right: str, providers_differ: bool | None, out_format: str) -> None:
    """Compare two observation dossiers."""
    left_data = _read_json(left)
    right_data = _read_json(right)

    service = StandardDifferentialFacetService()
    kwargs = {}
    if providers_differ is not None:
        kwargs["providers_differ"] = providers_differ

    report = service.compare_observations(left_data, right_data, **kwargs)
    exported = service.export_report(report)

    if out_format == "json":
        click.echo(json.dumps(exported, indent=2, ensure_ascii=False))
        return

    if out_format == "plain":
        click.echo(f"Report: {report.report_id}")
        click.echo(f"Overall Status: {report.overall_status}")
        click.echo(f"Digest: {report.summary_digest}")
        return

    # Rich table
    click.echo(f"Differential Report: {report.report_id} [{report.overall_status.upper()}]")
    click.echo(f"{'Dimension':<16} | {'Status':<10} | {'Conclusion':<20}")
    click.echo("-" * 52)
    for dim in report.dimensions:
        click.echo(f"{dim.dimension:<16} | {dim.status:<10} | {dim.conclusion_kind:<20}")
        for l in dim.limitations:
            click.echo(f"  └─ {l}")


@cli.command("claim-absence")
@click.argument("coverage_path", type=click.Path(exists=True))
def claim_absence_cmd(coverage_path: str) -> None:
    """Evaluate whether an absence claim is valid under declared coverage."""
    cov_data = _read_json(coverage_path)
    cov = CoverageDeclaration(
        scope=cov_data.get("scope", "dossier"),
        status=cov_data.get("status", "unknown"),
        truncated=bool(cov_data.get("truncated", False)),
        omitted_count=int(cov_data.get("omitted_count", 0)),
    )
    service = StandardDifferentialFacetService()
    claimable = service.validate_absence_claim(cov)
    click.echo(json.dumps({"absence_claimable": claimable, "status": cov.status, "truncated": cov.truncated}, indent=2))


@cli.command("verify")
@click.argument("report_path", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Exit with code 1 if overall status is unknown")
def verify_cmd(report_path: str, strict: bool) -> None:
    """Verify integrity of a differential report."""
    rep_data = _read_json(report_path)
    rep_id = rep_data.get("report_id", "")
    overall = rep_data.get("overall_status", "unknown")
    if not rep_id.startswith("rep:"):
        raise click.ClickException(f"Invalid report_id: {rep_id}")
    click.echo(f"Verified report {rep_id}: status={overall}")
    if strict and overall == "unknown":
        sys.exit(1)


@cli.command("export")
@click.argument("report_path", type=click.Path(exists=True))
def export_cmd(report_path: str) -> None:
    """Export machine-readable JSON certificate."""
    rep_data = _read_json(report_path)
    click.echo(json.dumps(rep_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
