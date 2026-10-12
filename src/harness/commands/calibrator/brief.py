"""Interactive HTML visual brief generation Click command."""

from __future__ import annotations

import webbrowser

import click

from harness.commands.calibrator.resolver import get_calibrator_service


@click.command("brief")
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
    help="Model parameter size in billions",
)
@click.option(
    "--workload",
    "-w",
    default="terminal_cli",
    help="Workload: terminal_cli | codebase_repo | mixed",
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
def calibrator_brief_cli(
    model_name: str,
    parameter_billions: float,
    workload: str,
    output: str | None,
    open_browser: bool,
) -> None:
    """Generate interactive HTML visual brief with Mermaid topology and empirical scorecard."""
    service = get_calibrator_service()
    rec = service.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
    )
    out_path = service.visual_brief(report_or_rec=rec, output_path=output)
    click.echo(f"HTML visual brief generated at:\n  {out_path}")

    if open_browser:
        webbrowser.open(out_path.as_uri())
