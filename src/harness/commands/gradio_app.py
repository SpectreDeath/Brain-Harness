"""Headless Click CLI commands for Gradio App Architect.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
from pathlib import Path
import sys

import click

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.gradio_app import (
    AppScaffoldConfigData,
    AppScaffoldResultData,
    DiagnosticReportData,
    GradioAppArchitectService,
)


def get_gradio_app_architect_service() -> GradioAppArchitectService:
    """Retrieve or bootstrap the GradioAppArchitect service singleton."""
    try:
        from plugins.integration_and_io.gradio_app_architect.main import plugin
        return plugin
    except Exception:
        # Fallback: bootstrap engine directly
        _ws_root = Path(__file__).resolve().parents[3]
        _skill_scripts = (
            _ws_root / ".agents" / "skills" / "gradio-app-architect" / "scripts"
        )
        if str(_skill_scripts) not in sys.path:
            sys.path.insert(0, str(_skill_scripts))

        from plugins.integration_and_io.gradio_app_architect.main import (
            GradioAppArchitectPlugin,
        )

        return GradioAppArchitectPlugin()


@click.group("gradio")
def gradio_group() -> None:
    """Gradio App Architect CLI — Production AI interface engineering & AST diagnostics."""
    pass


@gradio_group.command("inspect")
@click.argument("target", type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def inspect_cmd(target: str, json_output: bool) -> None:
    """Run AST static analysis against Eva J Patel's 5 production Gradio rubrics.

    TARGET can be a path to a Python file or raw Python code string.
    """
    target_p = Path(target)
    if target_p.exists() and target_p.is_file():
        source_code = target_p.read_text(encoding="utf-8")
        file_label = str(target_p)
    else:
        source_code = target
        file_label = "<cli-input>"

    svc = get_gradio_app_architect_service()
    report: DiagnosticReportData = svc.audit_code(source_code, file_path=file_label)

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
        return

    click.echo(f"Gradio AST Diagnostic Scorecard for '{report.target}':")
    click.echo(f"  Overall Status: {'PASSED' if report.passed else 'FAILED'}")
    click.echo("  Checks:")
    for c in report.checks:
        status_tag = "PASS" if c.passed else "FAIL"
        line_tag = f" (line {c.line_number})" if c.line_number else ""
        click.echo(f"    [{status_tag}] {c.name}{line_tag}: {c.message}")

    if report.metrics:
        click.echo("  Metrics:")
        for k, v in report.metrics.items():
            click.echo(f"    - {k}: {v}")


@gradio_group.command("scaffold")
@click.option("--name", "-n", default="my_gradio_app", help="Application name identifier")
@click.option(
    "--topology",
    "-t",
    default="blocks",
    type=click.Choice(["blocks", "chat", "interface"], case_sensitive=False),
    help="Interface layout topology",
)
@click.option(
    "--concurrency-limit",
    "-c",
    default=5,
    help="Queued concurrent execution bound",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    help="Target directory to write files",
)
@click.option(
    "--write/--no-write",
    "write_files",
    default=False,
    help="Write files to disk or display manifest",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def scaffold_cmd(
    name: str,
    topology: str,
    concurrency_limit: int,
    output_dir: str,
    write_files: bool,
    json_output: bool,
) -> None:
    """Scaffold a decoupled 3-layer production Gradio application."""
    svc = get_gradio_app_architect_service()
    cfg = AppScaffoldConfigData(
        app_name=name,
        topology=topology,
        enable_queue=True,
        concurrency_limit=concurrency_limit,
        output_dir=output_dir,
    )
    result: AppScaffoldResultData = svc.scaffold_app(cfg)

    if write_files:
        dest_dir = Path(output_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in result.files.items():
            out_file = dest_dir / fname
            out_file.write_text(content, encoding="utf-8")
        result.manifest["written_to"] = str(dest_dir.resolve())

    if json_output:
        click.echo(_json.dumps(result.model_dump(), indent=2))
        return

    click.echo(f"Gradio Application Scaffolding for '{name}':")
    click.echo(f"  Topology:          {topology.upper()}")
    click.echo(f"  Files Generated:   {len(result.files)}")
    for fname in result.files:
        click.echo(f"    + {fname}")
    if write_files:
        click.echo(f"  Destination:       {Path(output_dir).resolve()}")
    else:
        click.echo("  Status:            Preview (Use --write to output files)")


@gradio_group.command("brief")
@click.option("--output", "-o", default=None, help="Output file path for HTML brief")
def brief_cmd(output: str | None) -> None:
    """Generate interactive standalone HTML visual brief."""
    svc = get_gradio_app_architect_service()
    brief_path = svc.generate_visual_brief(output)
    click.echo(f"Gradio App Architect Visual Brief generated: {brief_path}")
