"""Terrain, satellite orbital pass, and imagery rendering standalone tools."""

from __future__ import annotations

from typing import Any
from ..async_runner import run_sync_safe
from ..engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge
from .analyst_tools import _build_area_dict


def gev_calculate_satellite_passes(
    lat: float,
    lon: float,
    sat_name: str = "ISS",
    norad_id: int = 25544,
    horizon_hours: int = 24,
) -> list[dict[str, Any]]:
    """Predict upcoming orbital overpasses over ground coordinates."""
    engine = resolve_gods_eye_view_engine()
    passes = run_sync_safe(
        engine.calculate_satellite_passes(
            lat=lat,
            lon=lon,
            sat_name=sat_name,
            norad_id=norad_id,
            horizon_hours=horizon_hours,
        )
    )
    return [p.model_dump() for p in passes]


def gev_render_sat_ortho(
    lat: float,
    lon: float,
    zoom: int = 21,
    size: int = 2048,
    outdir: str | None = None,
) -> dict[str, Any]:
    """Stitch high-resolution satellite orthomosaic from 3D Map Tiles."""
    engine = resolve_gods_eye_view_engine()
    res = run_sync_safe(
        engine.render_sat_ortho(
            lat=lat,
            lon=lon,
            zoom=zoom,
            size=size,
            outdir=outdir,
        )
    )
    return res.model_dump()


def gev_render_globe_snapshot(
    lat: float,
    lon: float,
    altitude_m: float = 1000.0,
    pitch: float = -45.0,
    heading: float = 0.0,
    style: str = "normal",
    outdir: str | None = None,
) -> dict[str, Any]:
    """Render photorealistic 3D Cesium globe snapshots with post-processing shaders."""
    engine = resolve_gods_eye_view_engine()
    res = run_sync_safe(
        engine.render_globe_snapshot(
            lat=lat,
            lon=lon,
            altitude_m=altitude_m,
            pitch=pitch,
            heading=heading,
            style=style,
            outdir=outdir,
        )
    )
    return res.model_dump()


def gev_get_terrain_height(
    points: list[dict[str, float]],
) -> dict[str, Any]:
    """Query terrain ground elevation above mean sea level for coordinate points."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_terrain_height", {"points": points}))


def gev_get_recent_imagery(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch recent Landsat/Sentinel/VIIRS optical satellite imagery metadata for a region."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Amazon Basin"}
    return run_sync_safe(bridge.query_mcp_tool("get_recent_imagery", {"area": area}))
