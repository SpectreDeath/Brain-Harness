#!/usr/bin/env python3
# /// script
# dependencies = ["click", "structlog", "pyyaml"]
# ///
"""Headless Click CLI Seam for Garf Reporting Architect.

Provides command-line query parsing, zero-network simulation,
tabular report egress dispatch, and workflow DAG execution.

Rule 10: Headless CLI Introspection Seams.
Rule 23 & Rule 50: UTF-8 standard stream reconfigure and sys.path precedence.
Rule 45 & Rule 49: Skill-to-IoC Micro-Kernel Seam Elevation via authoritative provider singleton.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Rule 23 & Rule 50: Explicitly reconfigure streams to UTF-8 and prepend workspace paths
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

workspace_root = Path(__file__).resolve().parents[4]
if str(workspace_root / "src") not in sys.path:
    sys.path.insert(0, str(workspace_root / "src"))
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

import click
import yaml

from harness.commands.garf import get_garf_reporting_service
from harness.services.garf_reporting import GarfWorkflowStep


def _resolve_query_text(query: str | None, query_file: str | None) -> str:
    """Resolve query text from string argument or file path."""
    if query:
        return query.strip()
    if query_file:
        p = Path(query_file)
        if not p.exists():
            raise click.BadParameter(f"Query file not found: {query_file}")
        return p.read_text(encoding="utf-8").strip()
    raise click.UsageError("Must provide either --query/-q or --query-file/-f")


@click.group()
def cli() -> None:
    """Garf Reporting Architect CLI Seam."""


@cli.command("parse")
@click.option("--query", "-q", default=None, help="SQL query string to parse.")
@click.option(
    "--query-file",
    "-f",
    default=None,
    type=click.Path(exists=False),
    help="Path to .sql file.",
)
@click.option(
    "--json-out", is_flag=True, help="Output parsed query specification as JSON."
)
def parse_cmd(query: str | None, query_file: str | None, json_out: bool) -> None:
    """Parse a reporting API SQL query into structured components."""
    query_text = _resolve_query_text(query, query_file)
    service = get_garf_reporting_service()
    spec = service.parse_query(query_text)
    data = {
        "title": spec.title,
        "resource_name": spec.resource_name,
        "fields": list(spec.fields),
        "filters": list(spec.filters),
        "sorts": list(spec.sorts),
        "limit": spec.limit,
        "column_names": list(spec.column_names),
        "dynamic_macros": dict(spec.dynamic_macros),
        "virtual_columns": [
            {
                "name": vc.name,
                "expression": vc.expression,
                "source_fields": list(vc.source_fields),
            }
            for vc in spec.virtual_columns
        ],
    }
    if json_out:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Title: {spec.title}")
        click.echo(f"Resource: {spec.resource_name}")
        click.echo(f"Columns: {', '.join(spec.column_names)}")
        click.echo(f"Filters: {', '.join(spec.filters) if spec.filters else 'None'}")
        if spec.limit:
            click.echo(f"Limit: {spec.limit}")
        if spec.virtual_columns:
            click.echo(f"Virtual Columns: {len(spec.virtual_columns)}")
            for vc in spec.virtual_columns:
                click.echo(f"  - {vc.name} = {vc.expression}")


@cli.command("simulate")
@click.option("--query", "-q", default=None, help="SQL query string to simulate.")
@click.option(
    "--query-file",
    "-f",
    default=None,
    type=click.Path(exists=False),
    help="Path to .sql file.",
)
@click.option(
    "--rows", "-r", default=5, type=int, help="Number of synthetic rows to generate."
)
@click.option(
    "--seed",
    "-s",
    default=42,
    type=int,
    help="PRNG seed for simulation reproducibility.",
)
@click.option("--json-out", is_flag=True, help="Output simulated rows as JSON.")
def simulate_cmd(
    query: str | None, query_file: str | None, rows: int, seed: int, json_out: bool
) -> None:
    """Simulate a synthetic tabular report from a query specification."""
    query_text = _resolve_query_text(query, query_file)
    service = get_garf_reporting_service()
    spec = service.parse_query(query_text)
    batch = service.simulate_report(spec, row_count=rows, seed=seed)
    if json_out:
        click.echo(json.dumps(batch.to_dict_list(), indent=2))
    else:
        click.echo(f"Simulated {batch.row_count} rows for [{batch.query_title}]:")
        click.echo(" | ".join(batch.column_names))
        click.echo("-" * 40)
        for r in batch.rows:
            click.echo(" | ".join(str(val) for val in r))


@cli.command("export")
@click.option("--query", "-q", default=None, help="SQL query string to execute.")
@click.option(
    "--query-file",
    "-f",
    default=None,
    type=click.Path(exists=False),
    help="Path to .sql file.",
)
@click.option(
    "--dest-type",
    "-t",
    type=click.Choice(["csv", "json", "sqlite", "duckdb", "console"]),
    default="json",
)
@click.option("--dest-path", "-p", default="output.json", help="Path for output file.")
@click.option("--rows", "-r", default=5, type=int, help="Number of rows to simulate.")
@click.option(
    "--seed",
    "-s",
    default=42,
    type=int,
    help="PRNG seed for simulation reproducibility.",
)
@click.option("--json-out", is_flag=True, help="Output execution receipt as JSON.")
def export_cmd(
    query: str | None,
    query_file: str | None,
    dest_type: str,
    dest_path: str,
    rows: int,
    seed: int,
    json_out: bool,
) -> None:
    """Execute query simulation and export tabular report to destination file."""
    query_text = _resolve_query_text(query, query_file)
    service = get_garf_reporting_service()
    spec = service.parse_query(query_text)
    batch = service.simulate_report(spec, row_count=rows, seed=seed)
    receipt = service.write_report(
        batch, destination_type=dest_type, destination_path=dest_path
    )

    if json_out:
        out = {
            "status": receipt.status,
            "operation": receipt.operation,
            "row_count": receipt.row_count,
            "elapsed_seconds": receipt.elapsed_seconds,
            "details": dict(receipt.details),
        }
        click.echo(json.dumps(out, indent=2))
    else:
        click.echo(f"Export status: {receipt.status} ({receipt.operation})")
        click.echo(f"Wrote {receipt.row_count} rows in {receipt.elapsed_seconds}s")
        for k, v in receipt.details:
            click.echo(f"  {k}: {v}")


@cli.command("workflow")
@click.option(
    "--config",
    "-c",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to YAML or JSON workflow configuration file.",
)
@click.option(
    "--param",
    "-p",
    "params",
    multiple=True,
    help="Context parameters formatted as key=value.",
)
@click.option("--json-out", is_flag=True, help="Output execution receipt as JSON.")
def workflow_cmd(config_path: str, params: tuple[str, ...], json_out: bool) -> None:
    """Execute a multi-step analytical workflow DAG from configuration."""
    cfg_file = Path(config_path)
    content = cfg_file.read_text(encoding="utf-8")

    if cfg_file.suffix in (".yaml", ".yml"):
        raw_cfg = yaml.safe_load(content) or {}
    else:
        raw_cfg = json.loads(content) or {}

    raw_steps = raw_cfg.get("steps") if isinstance(raw_cfg, dict) else raw_cfg
    if not isinstance(raw_steps, list):
        raise click.UsageError("Workflow configuration must contain a list of steps")

    context_dict: dict[str, Any] = {}
    if (
        isinstance(raw_cfg, dict)
        and "context" in raw_cfg
        and isinstance(raw_cfg["context"], dict)
    ):
        context_dict.update(raw_cfg["context"])

    for item in params:
        if "=" in item:
            k, v = item.split("=", 1)
            context_dict[k.strip()] = v.strip()

    steps = [
        GarfWorkflowStep(
            step_id=str(s["step_id"]),
            step_type=str(s["step_type"]),
            query_path=s.get("query_path"),
            writer_type=s.get("writer_type"),
            destination=s.get("destination"),
            depends_on=tuple(s.get("depends_on") or ()),
            sql_query=s.get("sql_query"),
        )
        for s in raw_steps
    ]

    service = get_garf_reporting_service()
    receipt = service.run_workflow(steps, context_params=context_dict)

    if json_out:
        out = {
            "status": receipt.status,
            "operation": receipt.operation,
            "row_count": receipt.row_count,
            "elapsed_seconds": receipt.elapsed_seconds,
            "details": dict(receipt.details),
        }
        click.echo(json.dumps(out, indent=2))
    else:
        click.echo(f"Workflow status: {receipt.status} ({receipt.operation})")
        click.echo(f"Executed steps:  {receipt.get_detail('executed_steps')}")
        click.echo(f"Total rows:      {receipt.row_count}")
        click.echo(f"Elapsed time:    {receipt.elapsed_seconds}s")


if __name__ == "__main__":
    cli()
