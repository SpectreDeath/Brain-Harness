"""Headless Click CLI commands for Google Garf Declarative SQL Reporting.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog
import yaml

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext
from harness.services.garf_reporting import (
    GARF_REPORTING_SERVICE_KEY,
    DefaultGarfReportingService,
    GarfReportingService,
    GarfWorkflowStep,
)

logger = structlog.get_logger(__name__)


def get_garf_reporting_service(
    context: ServiceContext | None = None,
) -> GarfReportingService:
    """Retrieve or bootstrap the GarfReportingService singleton."""
    if context is not None:
        svc = context.optional(GARF_REPORTING_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fall back to plugin singleton or direct engine
    try:
        from plugins.data_engineering.garf_reporting_pipeline.main import (
            plugin as garf_plugin,
        )

        return garf_plugin
    except Exception as exc:
        logger.debug("garf_plugin_fallback_failed", error=str(exc))
        return DefaultGarfReportingService()


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


def garf_parse_cmd(
    query: str | None = None, query_file: str | None = None
) -> dict[str, Any]:
    """Parse reporting SQL query into structured dictionary."""
    query_text = _resolve_query_text(query, query_file)
    svc = get_garf_reporting_service()
    spec = svc.parse_query(query_text)
    return {
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


def garf_simulate_cmd(
    query: str | None = None,
    query_file: str | None = None,
    rows: int = 5,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Simulate synthetic report matching query specification."""
    query_text = _resolve_query_text(query, query_file)
    svc = get_garf_reporting_service()
    spec = svc.parse_query(query_text)
    batch = svc.simulate_report(spec, row_count=rows, seed=seed)
    return batch.to_dict_list()


def garf_export_cmd(
    query: str | None = None,
    query_file: str | None = None,
    dest_type: str = "json",
    dest_path: str = "output.json",
    rows: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Simulate and export report to destination."""
    query_text = _resolve_query_text(query, query_file)
    svc = get_garf_reporting_service()
    spec = svc.parse_query(query_text)
    batch = svc.simulate_report(spec, row_count=rows, seed=seed)
    receipt = svc.write_report(
        batch, destination_type=dest_type, destination_path=dest_path
    )
    return {
        "status": receipt.status,
        "operation": receipt.operation,
        "row_count": receipt.row_count,
        "elapsed_seconds": receipt.elapsed_seconds,
        "details": dict(receipt.details),
    }


def garf_workflow_cmd(
    config_path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute analytical workflow DAG from configuration."""
    cfg_file = Path(config_path)
    content = cfg_file.read_text(encoding="utf-8")
    if cfg_file.suffix in (".yaml", ".yml"):
        raw_cfg = yaml.safe_load(content) or {}
    else:
        raw_cfg = _json.loads(content) or {}

    raw_steps = raw_cfg.get("steps") if isinstance(raw_cfg, dict) else raw_cfg
    if not isinstance(raw_steps, list):
        raise ValueError("Workflow configuration must contain a list of steps")

    context_dict: dict[str, Any] = {}
    if (
        isinstance(raw_cfg, dict)
        and "context" in raw_cfg
        and isinstance(raw_cfg["context"], dict)
    ):
        context_dict.update(raw_cfg["context"])

    if params:
        context_dict.update(params)

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

    svc = get_garf_reporting_service()
    receipt = svc.run_workflow(steps, context_params=context_dict)
    return {
        "status": receipt.status,
        "operation": receipt.operation,
        "row_count": receipt.row_count,
        "elapsed_seconds": receipt.elapsed_seconds,
        "details": dict(receipt.details),
    }


@click.group("garf")
def garf_group() -> None:
    """Google Garf Declarative SQL Reporting & Analytical Workflow DAGs."""


@garf_group.command("parse")
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
    data = garf_parse_cmd(query=query, query_file=query_file)

    if json_out:
        click.echo(_json.dumps(data, indent=2))
    else:
        click.echo(f"Title:           {data['title']}")
        click.echo(f"Resource:        {data['resource_name']}")
        click.echo(f"Columns:         {', '.join(data['column_names'])}")
        click.echo(
            f"Filters:         {', '.join(data['filters']) if data['filters'] else 'None'}"
        )
        if data["limit"]:
            click.echo(f"Limit:           {data['limit']}")
        if data["virtual_columns"]:
            click.echo(f"Virtual Columns: {len(data['virtual_columns'])}")
            for vc in data["virtual_columns"]:
                click.echo(f"  - {vc['name']} = {vc['expression']}")


@garf_group.command("simulate")
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
    svc = get_garf_reporting_service()
    spec = svc.parse_query(query_text)
    batch = svc.simulate_report(spec, row_count=rows, seed=seed)

    if json_out:
        click.echo(_json.dumps(batch.to_dict_list(), indent=2))
    else:
        click.echo(f"Simulated {batch.row_count} rows for [{batch.query_title}]:")
        click.echo(" | ".join(batch.column_names))
        click.echo("-" * 50)
        for r in batch.rows:
            click.echo(" | ".join(str(val) for val in r))


@garf_group.command("export")
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
@click.option(
    "--rows", "-r", default=5, type=int, help="Number of rows to simulate."
)
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
    data = garf_export_cmd(
        query=query,
        query_file=query_file,
        dest_type=dest_type,
        dest_path=dest_path,
        rows=rows,
        seed=seed,
    )

    if json_out:
        click.echo(_json.dumps(data, indent=2))
    else:
        click.echo(f"Export status:   {data['status']} ({data['operation']})")
        click.echo(f"Wrote {data['row_count']} rows in {data['elapsed_seconds']}s")
        for k, v in data["details"].items():
            click.echo(f"  {k}: {v}")


@garf_group.command("workflow")
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
def workflow_cmd(
    config_path: str, params: tuple[str, ...], json_out: bool
) -> None:
    """Execute a multi-step analytical workflow DAG from configuration."""
    param_dict = {}
    for item in params:
        if "=" in item:
            k, v = item.split("=", 1)
            param_dict[k.strip()] = v.strip()

    data = garf_workflow_cmd(config_path, params=param_dict)

    if json_out:
        click.echo(_json.dumps(data, indent=2))
    else:
        click.echo(f"Workflow status: {data['status']} ({data['operation']})")
        click.echo(
            f"Executed steps:  {data['details'].get('executed_steps', 'N/A')}"
        )
        click.echo(f"Total rows:      {data['row_count']}")
        click.echo(f"Elapsed time:    {data['elapsed_seconds']}s")
