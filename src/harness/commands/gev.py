"""God's Eye View (GEV) Planetary Intelligence and OSINT CLI Commands.

Rules enforced:
- Rule 6: Single-source co-located Click group declaration.
- Rule 10: Headless CLI inspection and export seams (--json).
- Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

# Rule 23: Windows UTF-8 stream codec entrypoint invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.commands._utils import _run_async
from harness.services.gods_eye_view import (
    attach_provenance_envelope,
    resolve_gods_eye_view,
)


@click.group("gev")
def gev_group() -> None:
    """God's Eye View — Planetary OSINT, real-time telemetry feeds, and 3D geospatial rendering."""


@gev_group.command("status")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON status payload")
def gev_status_cmd(json_output: bool) -> None:
    """Probe runtime environment, Node.js bridge availability, and cache configuration."""
    from plugins.geospatial_and_osint.gods_eye_view.cli_bridge import NodeCliBridge
    bridge = NodeCliBridge()
    node_avail = bridge.is_node_available()
    tools_dir = bridge.tools_dir
    try:
        tools_exist = Path(tools_dir).exists()
    except (PermissionError, OSError):
        tools_exist = False

    payload = {
        "status": "ok",
        "node_available": node_avail,
        "tools_directory": tools_dir,
        "tools_directory_exists": tools_exist,
        "subgroups": [
            "analyst_and_briefs",
            "aviation_and_maritime",
            "environmental_and_disasters",
            "tactical_and_space",
            "geospatial_rendering",
        ],
        "offline_simulation_fallback": True,
    }
    envelope = attach_provenance_envelope(payload, source_mode="live", ttl_seconds=60.0)

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho("=" * 68, fg="cyan")
    click.secho(" GOD'S EYE VIEW (GEV) — RUNTIME STATUS & CAPABILITIES", fg="cyan", bold=True)
    click.secho("=" * 68, fg="cyan")
    click.echo(f"  Node.js Runtime : {'[FOUND]' if node_avail else '[NOT FOUND]'}")
    click.echo(f"  Tools Directory : {tools_dir} ({'[EXISTS]' if tools_exist else '[MISSING]'})")
    click.echo(f"  Simulation Mode : Offline fallback enabled when air-gapped")
    click.echo("  Subgroups       : 5 domains (Analyst, Flights/Vessels, Hazards, Space, 3D Rendering)")


@gev_group.command("brief")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--radius-km", type=float, default=250.0, help="Search radius in kilometers")
@click.option("--query", "query_text", type=str, default=None, help="Optional text query or analyst focus")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_brief_cmd(lat: float, lon: float, radius_km: float, query_text: str | None, json_output: bool) -> None:
    """Generate composite multi-domain situation overview for an area."""
    svc = resolve_gods_eye_view()
    res = _run_async(svc.situation_brief(lat=lat, lon=lon, radius_km=radius_km))
    envelope = attach_provenance_envelope(
        res,
        source_mode="simulated_fallback" if not getattr(res, "is_live", True) else "live",
        ttl_seconds=30.0,
    )

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho(f"--- Situation Brief ({lat:.4f}, {lon:.4f}) radius={radius_km}km ---", fg="cyan", bold=True)
    for line in getattr(res, "summary_lines", []):
        click.echo(f"  • {line}")


@gev_group.command("flights")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--radius-km", type=float, default=150.0, help="Search radius in km")
@click.option("--callsign", type=str, default=None, help="Callsign filter")
@click.option("--military", is_flag=True, help="Filter strictly for military flights")
@click.option("--limit", type=int, default=50, help="Maximum flights to return")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_flights_cmd(lat: float, lon: float, radius_km: float, callsign: str | None, military: bool, limit: int, json_output: bool) -> None:
    """Fetch live or simulated aviation transponder vectors."""
    svc = resolve_gods_eye_view()
    d_lat = radius_km / 111.0
    d_lon = radius_km / 111.0
    bbox = [lat + d_lat, lat - d_lat, lon - d_lon, lon + d_lon]

    flights = _run_async(svc.fetch_flights(bbox=bbox, callsign=callsign, military_only=military, limit=limit))
    envelope = attach_provenance_envelope(
        {"total": len(flights), "flights": [f.model_dump() if hasattr(f, "model_dump") else f for f in flights]},
        source_mode="live" if flights else "simulated_fallback",
        ttl_seconds=15.0,
    )

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho(f"Discovered {len(flights)} flight(s) within {radius_km}km:", fg="green", bold=True)
    for f in flights[:limit]:
        cs = getattr(f, "callsign", "N/A") or "N/A"
        alt = getattr(f, "altitude_m", 0.0) or 0.0
        mil = "[MILITARY]" if getattr(f, "military", False) else ""
        click.echo(f"  • {getattr(f, 'icao24', 'UNKNOWN'):8} | {cs:10} | Alt: {alt:6.0f}m {mil}")


@gev_group.command("vessels")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--radius-km", type=float, default=200.0, help="Search radius in km")
@click.option("--name", "name_filter", type=str, default=None, help="Vessel name filter")
@click.option("--limit", type=int, default=50, help="Maximum vessels to return")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_vessels_cmd(lat: float, lon: float, radius_km: float, name_filter: str | None, limit: int, json_output: bool) -> None:
    """Retrieve real-time maritime AIS vessel records."""
    svc = resolve_gods_eye_view()
    d_lat = radius_km / 111.0
    d_lon = radius_km / 111.0
    bbox = [lat + d_lat, lat - d_lat, lon - d_lon, lon + d_lon]

    vessels = _run_async(svc.fetch_vessels(bbox=bbox, limit=limit))
    if name_filter:
        vessels = [v for v in vessels if name_filter.lower() in getattr(v, "name", "").lower()]

    envelope = attach_provenance_envelope(
        {"total": len(vessels), "vessels": [v.model_dump() if hasattr(v, "model_dump") else v for v in vessels]},
        source_mode="live" if vessels else "simulated_fallback",
        ttl_seconds=30.0,
    )

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho(f"Discovered {len(vessels)} vessel(s) within {radius_km}km:", fg="blue", bold=True)
    for v in vessels[:limit]:
        click.echo(f"  • MMSI: {getattr(v, 'mmsi', 'UNKNOWN'):10} | {getattr(v, 'name', 'UNKNOWN'):20} | Type: {getattr(v, 'ship_type', 'Unknown')}")


@gev_group.command("hazards")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--radius-km", type=float, default=300.0, help="Search radius in km")
@click.option("--kind", type=click.Choice(["all", "earthquakes", "fires", "cyclones", "weather"]), default="all", help="Hazard category")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_hazards_cmd(lat: float, lon: float, radius_km: float, kind: str, json_output: bool) -> None:
    """Fetch environmental telemetry: earthquakes, active fires, cyclones, and weather."""
    svc = resolve_gods_eye_view()
    results: dict[str, Any] = {}

    if kind in ("all", "earthquakes"):
        eqs = _run_async(svc.fetch_earthquakes(lat=lat, lon=lon, radius_km=radius_km))
        results["earthquakes"] = [e.model_dump() if hasattr(e, "model_dump") else e for e in eqs]
    if kind in ("all", "fires"):
        d_lat = radius_km / 111.0
        d_lon = radius_km / 111.0
        bbox = [lat + d_lat, lat - d_lat, lon - d_lon, lon + d_lon]
        fires = _run_async(svc.fetch_firms_hotspots(bbox=bbox))
        results["fires"] = [f.model_dump() if hasattr(f, "model_dump") else f for f in fires]
    if kind in ("all", "cyclones"):
        cycs = _run_async(svc.get_cyclones(lat=lat, lon=lon, radius_km=radius_km))
        results["cyclones"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in cycs]
    if kind in ("all", "weather"):
        w = _run_async(svc.get_weather(lat=lat, lon=lon))
        results["weather"] = w.model_dump() if hasattr(w, "model_dump") else w

    envelope = attach_provenance_envelope(results, source_mode="live", ttl_seconds=60.0)

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho(f"Environmental Hazards & Observations around ({lat:.2f}, {lon:.2f}):", fg="yellow", bold=True)
    if "earthquakes" in results:
        click.echo(f"  • Earthquakes : {len(results['earthquakes'])} recorded")
    if "fires" in results:
        click.echo(f"  • Active Fires: {len(results['fires'])} hotspot(s)")
    if "cyclones" in results:
        click.echo(f"  • Cyclones    : {len(results['cyclones'])} active advisory(ies)")
    if "weather" in results:
        w_obj = results["weather"]
        summary = w_obj.get("summary") if isinstance(w_obj, dict) else getattr(w_obj, "summary", "")
        click.echo(f"  • Weather     : {summary or 'Conditions fetched'}")


@gev_group.command("spatial")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--radius-km", type=float, default=250.0, help="Radius in km")
@click.option("--kind", type=click.Choice(["infra", "sat-passes", "military", "cctv"]), default="infra", help="Spatial query kind")
@click.option("--query", "query_text", type=str, default=None, help="Text query filter")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_spatial_cmd(lat: float, lon: float, radius_km: float, kind: str, query_text: str | None, json_output: bool) -> None:
    """Query tactical awareness, orbital satellite passes, infrastructure, or CCTV assets."""
    svc = resolve_gods_eye_view()
    payload: Any = None

    if kind == "infra":
        items = _run_async(svc.query_infrastructure(infra_type="all", query=query_text, lat=lat, lon=lon, radius_km=radius_km))
        payload = {"items": [i.model_dump() if hasattr(i, "model_dump") else i for i in items]}
    elif kind == "sat-passes":
        passes = _run_async(svc.calculate_satellite_passes(lat=lat, lon=lon, horizon_hours=24))
        payload = {"passes": [p.model_dump() if hasattr(p, "model_dump") else p for p in passes]}
    elif kind == "military":
        mil = _run_async(svc.query_military_awareness(lat=lat, lon=lon, radius_km=radius_km))
        payload = mil.model_dump() if hasattr(mil, "model_dump") else mil
    elif kind == "cctv":
        cams = _run_async(svc.find_cctv_cameras(lat=lat, lon=lon, radius_km=radius_km))
        payload = {"cameras": [c.model_dump() if hasattr(c, "model_dump") else c for c in cams]}

    envelope = attach_provenance_envelope(payload, source_mode="live", ttl_seconds=60.0)

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    click.secho(f"Spatial Intelligence [{kind}] ({lat:.4f}, {lon:.4f}) radius={radius_km}km:", fg="magenta", bold=True)
    if isinstance(payload, dict):
        for k, v in payload.items():
            count_str = len(v) if isinstance(v, list) else v
            click.echo(f"  • {k}: {count_str}")


@gev_group.command("render")
@click.option("--lat", type=float, required=True, help="Center latitude")
@click.option("--lon", type=float, required=True, help="Center longitude")
@click.option("--mode", type=click.Choice(["globe", "ortho", "streetview", "terrain", "imagery"]), default="globe", help="Rendering engine")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None, help="Output destination path")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gev_render_cmd(lat: float, lon: float, mode: str, output_path: Path | None, json_output: bool) -> None:
    """Render 3D Cesium globe snapshots, satellite orthomosaics, or Street View headings."""
    svc = resolve_gods_eye_view()
    outdir = str(output_path.parent) if output_path else None

    if mode == "globe":
        res = _run_async(svc.render_globe_snapshot(lat=lat, lon=lon, outdir=outdir))
    elif mode == "ortho":
        res = _run_async(svc.render_sat_ortho(lat=lat, lon=lon, outdir=outdir))
    elif mode == "streetview":
        res = _run_async(svc.capture_streetview_headings(lat=lat, lon=lon, outdir=outdir))
    elif mode == "terrain":
        res = _run_async(svc.get_terrain_height([{"lat": lat, "lon": lon}]))
    else:
        res = _run_async(svc.get_recent_imagery(lat=lat, lon=lon))

    envelope = attach_provenance_envelope(
        res,
        source_mode="live" if getattr(res, "status", "") == "ok" else "simulated_fallback",
        ttl_seconds=300.0,
    )

    if json_output:
        click.echo(json.dumps(envelope, indent=2))
        return

    status = getattr(res, "status", "ok")
    path_val = getattr(res, "output_path", str(output_path or "rendered_asset"))
    click.secho(f"Render [{mode}] completed with status: {status}", fg="green" if status == "ok" else "yellow")
    click.echo(f"  Output: {path_val}")
