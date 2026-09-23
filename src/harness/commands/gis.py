"""Headless Click CLI commands for Open-Source GIS Architecture & Routing.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click
import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext
from harness.services.open_source_gis import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    DefaultOpenSourceGisService,
    FalconViewRestrictedDomainError,
    OpenSourceGisService,
    SpatialWorkloadProfile,
)

logger = structlog.get_logger(__name__)


def get_open_source_gis_service(
    context: ServiceContext | None = None,
) -> OpenSourceGisService:
    """Retrieve or bootstrap the OpenSourceGisService singleton."""
    if context is not None:
        svc = context.optional(OPEN_SOURCE_GIS_SERVICE_KEY)
        if svc is not None:
            return svc

    try:
        from plugins.geospatial_and_osint.open_source_gis.main import (
            plugin as gis_plugin,
        )

        return gis_plugin
    except Exception as exc:
        logger.debug("gis_plugin_fallback_failed", error=str(exc))
        return DefaultOpenSourceGisService()


@click.group("gis")
def gis_group() -> None:
    """Open-Source GIS analytical engine selection, CRS safety & topology auditing."""


@gis_group.command("route")
@click.option("--domain", "-d", required=True, help="Spatial analytical domain (e.g. lidar_hydrology, terrain_morphometry)")
@click.option("--geometry-type", "-g", default="vector_polygon", help="Geometry structure (point_cloud, raster_dem, etc.)")
@click.option("--format", "-f", "formats", multiple=True, help="Input data formats (LAS, GeoTIFF, etc.)")
@click.option("--sector", "-s", default="civilian", help="Operational sector")
@click.option("--analysis", "-a", default="", help="Specific analytical operation (twi, moran_i, etc.)")
@click.option("--has-lidar", is_flag=True, help="Workload contains LiDAR point clouds")
@click.option("--needs-statistics", is_flag=True, help="Requires spatial econometrics")
@click.option("--needs-mobile", is_flag=True, help="Requires field GPS / mobile surveying")
@click.option("--generate-brief", is_flag=True, help="Render Stage 5 interactive HTML visual brief")
@click.option("--json-out", is_flag=True, help="Emit raw JSON output")
def route_command(
    domain: str,
    geometry_type: str,
    formats: tuple[str, ...],
    sector: str,
    analysis: str,
    has_lidar: bool,
    needs_statistics: bool,
    needs_mobile: bool,
    generate_brief: bool,
    json_out: bool,
) -> None:
    """Route spatial workload to optimal primary and secondary open-source GIS engines."""
    service = get_open_source_gis_service()

    try:
        profile = SpatialWorkloadProfile(
            geometry_type=geometry_type,
            domain=domain,
            data_formats=formats,
            sector=sector,
            analysis=analysis,
            has_lidar=has_lidar,
            needs_statistics=needs_statistics,
            needs_mobile=needs_mobile,
        )
    except FalconViewRestrictedDomainError as err:
        click.secho(f"[SAFETY HALT] {err}", fg="red", err=True)
        sys.exit(2)

    result = service.route_workload(profile)

    brief_path = None
    if generate_brief:
        brief_res = service.generate_visual_brief(profile=profile, selection=result)
        brief_path = brief_res.report_path

    if json_out:
        payload = {
            "routing_path": result.routing_path,
            "composite_score": result.composite_score,
            "primary": {
                "name": result.primary.engine.name,
                "fitness_score": result.primary.fitness_score,
                "license": result.primary.engine.license,
            },
            "secondary": {
                "name": result.secondary.engine.name,
                "fitness_score": result.secondary.fitness_score,
            }
            if result.secondary
            else None,
            "rationale": result.rationale,
            "visual_brief_path": brief_path,
        }
        click.echo(_json.dumps(payload, indent=2))
        return

    click.secho("=== Open-Source GIS Routing Result ===", fg="cyan", bold=True)
    click.echo(f"Routing Path: {result.routing_path}")
    click.echo(f"Primary Engine: {result.primary.engine.name} (Fitness: {result.primary.fitness_score:.2f})")
    click.echo(f"  Rationale: {result.rationale}")
    if result.secondary:
        click.echo(f"Secondary Engine: {result.secondary.engine.name} (Fitness: {result.secondary.fitness_score:.2f})")
    if brief_path:
        click.secho(f"Visual Brief: {brief_path}", fg="green")


@gis_group.command("validate")
@click.option("--pipeline-file", "-f", type=click.Path(exists=True), required=True, help="Path to pipeline JSON file")
def validate_command(pipeline_file: str) -> None:
    """Validate spatial execution pipeline DAG for CRS projection safety."""
    service = get_open_source_gis_service()
    raw = _json.loads(Path(pipeline_file).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "steps" in raw:
        raw = raw["steps"]

    valid, messages, dag = service.validate_pipeline_dag(raw)
    if valid:
        click.secho(f"[PASS] Pipeline DAG valid with {dag.total_steps if dag else len(raw)} steps.", fg="green")
        for m in messages:
            click.echo(f"  - {m}")
    else:
        click.secho("[FAIL] Pipeline DAG has CRS or integrity errors:", fg="red", err=True)
        for m in messages:
            click.echo(f"  - {m}", err=True)
        sys.exit(1)


@gis_group.command("architect")
@click.option("--profile-json", "-p", type=click.Path(exists=True), required=True, help="Workload JSON profile")
@click.option("--pipeline-json", "-d", type=click.Path(exists=True), default=None, help="Optional pipeline steps JSON")
@click.option("--generate-brief/--no-brief", default=True, help="Render Stage 5 HTML visual brief")
def architect_command(
    profile_json: str,
    pipeline_json: str | None,
    generate_brief: bool,
) -> None:
    """Execute end-to-end spatial architecture interrogation and print structured receipt."""
    service = get_open_source_gis_service()
    prof_data = _json.loads(Path(profile_json).read_text(encoding="utf-8"))
    steps = None
    if pipeline_json:
        raw_steps = _json.loads(Path(pipeline_json).read_text(encoding="utf-8"))
        steps = raw_steps.get("steps") if isinstance(raw_steps, dict) else raw_steps

    receipt = service.architect_workload(
        profile_data=prof_data,
        pipeline_steps=steps,
        generate_brief=generate_brief,
    )
    click.echo(receipt.receipt_markdown)
