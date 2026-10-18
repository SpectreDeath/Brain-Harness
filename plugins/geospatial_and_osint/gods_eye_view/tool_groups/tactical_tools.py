"""Tactical, infrastructure, and surveillance standalone tools."""

from __future__ import annotations

from typing import Any
from ..async_runner import run_sync_safe
from ..engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge
from .analyst_tools import _build_area_dict


def gev_query_military_awareness(
    lat: float,
    lon: float,
    radius_km: float = 250.0,
    include_bases: bool = True,
) -> dict[str, Any]:
    """Compute tactical military awareness corridor and air/naval assets."""
    engine = resolve_gods_eye_view_engine()
    summary = run_sync_safe(
        engine.query_military_awareness(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            include_bases=include_bases,
        )
    )
    return summary.model_dump()


def gev_query_infrastructure(
    infra_type: str,
    query: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> list[dict[str, Any]]:
    """Query offline global submarine cables, datacenters, dams, and landing points."""
    engine = resolve_gods_eye_view_engine()
    records = engine.query_infrastructure(
        infra_type=infra_type,
        query=query,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )
    return [r.model_dump() for r in records]


def gev_capture_streetview_headings(
    lat: float,
    lon: float,
    fov: int = 90,
    pitch: int = 0,
    neighbors: bool = False,
    outdir: str | None = None,
) -> dict[str, Any]:
    """Capture 8 compass headings (360 ground view) via Static Street View."""
    engine = resolve_gods_eye_view_engine()
    res = run_sync_safe(
        engine.capture_streetview_headings(
            lat=lat,
            lon=lon,
            fov=fov,
            pitch=pitch,
            neighbors=neighbors,
            outdir=outdir,
        )
    )
    return res.model_dump()


def gev_find_cctv_cameras(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search public traffic and highway camera installations in an area."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Downtown"}
    return run_sync_safe(bridge.query_mcp_tool("find_cctv_cameras", {"area": area, "limit": limit}))


def gev_get_cctv_snapshot(
    camera_id: str,
) -> dict[str, Any]:
    """Retrieve latest still snapshot frame from public camera."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_cctv_snapshot", {"camera_id": camera_id}))
