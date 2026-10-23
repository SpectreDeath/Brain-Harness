# -*- coding: utf-8 -*-
"""Headless Click CLI seam for Python Diagrams-as-Code (Rule 10, Rule 23, Rule 50)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import click

# Ensure UTF-8 streams per Rule 23 and Rule 50
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure local script directory is on sys.path
SCRIPT_DIR = Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pda_diagram_engine import PythonDiagramsEngine


@click.group(name="diagrams")
def cli() -> None:
    """Python Diagrams-as-Code command group."""
    pass


@cli.command(name="presets")
@click.option("--json-out", is_flag=True, help="Output preset list as JSON.")
def list_presets(json_out: bool) -> None:
    """List available canonical architecture diagram presets."""
    presets = [
        {
            "name": "three_tier_web_app",
            "title": "Three-Tier Scaled Web Platform",
            "provider": "AWS",
            "tiers": ["Presentation", "Application", "Database"],
        },
        {
            "name": "event_driven_microservices",
            "title": "Event-Driven Microservices Architecture",
            "provider": "AWS",
            "tiers": ["API Gateway", "Streaming & Queue", "Workers", "Persistence"],
        },
        {
            "name": "kubernetes_cluster",
            "title": "Kubernetes Ingress and Pod Architecture",
            "provider": "Kubernetes",
            "tiers": ["Cluster Boundary", "Default Namespace"],
        },
    ]

    if json_out:
        click.echo(json.dumps(presets, indent=2))
    else:
        click.echo("Available Architecture Presets:")
        for p in presets:
            click.echo(f"  • {p['name']} ({p['title']}) [{p['provider']}]")


@cli.command(name="preset")
@click.argument("name")
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), help="Target Python output path.")
def generate_preset(name: str, output: str | None) -> None:
    """Generate Python diagram code from a canonical architecture preset."""
    try:
        spec = PythonDiagramsEngine.get_canonical_preset(name)
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    code = PythonDiagramsEngine.generate_code(spec)
    if output:
        out_path = Path(output)
        out_path.write_text(code, encoding="utf-8")
        click.echo(f"Wrote {len(code.encode('utf-8'))} bytes to {out_path.resolve()}")
    else:
        click.echo(code)


@cli.command(name="lint")
@click.argument("script_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--json-out", is_flag=True, help="Output diagnostics as JSON.")
def lint_script(script_file: str, json_out: bool) -> None:
    """Statically lint a diagram Python script for syntax, anti-patterns, and headless compatibility."""
    path = Path(script_file)
    content = path.read_text(encoding="utf-8", errors="ignore")
    report = PythonDiagramsEngine.lint_script_code(content)

    if json_out:
        data = {
            "valid": report.valid,
            "errors": list(report.errors),
            "warnings": list(report.warnings),
            "node_count": report.node_count,
            "cluster_count": report.cluster_count,
            "providers_used": list(report.providers_used),
        }
        click.echo(json.dumps(data, indent=2))
    else:
        status_str = "PASSED" if report.valid else "FAILED"
        click.echo(f"Lint Status: {status_str}")
        click.echo(f"  Nodes detected: {report.node_count}")
        click.echo(f"  Clusters detected: {report.cluster_count}")
        click.echo(f"  Providers: {', '.join(report.providers_used) or 'None'}")

        if report.errors:
            click.echo("\nErrors:")
            for err in report.errors:
                click.echo(f"  [ERROR] {err}")

        if report.warnings:
            click.echo("\nWarnings:")
            for warn in report.warnings:
                click.echo(f"  [WARN]  {warn}")

    if not report.valid:
        sys.exit(1)


if __name__ == "__main__":
    cli()
