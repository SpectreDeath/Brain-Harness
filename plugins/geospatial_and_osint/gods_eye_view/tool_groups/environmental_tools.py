"""Environmental and natural hazard OSINT standalone tools."""

from __future__ import annotations

from typing import Any
from ..async_runner import run_sync_safe
from ..engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge
from .analyst_tools import _build_area_dict


def gev_get_weather(
    place: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any]:
    """Retrieve current weather conditions at target coordinate or location name."""
    bridge = resolve_node_cli_bridge()
    args: dict[str, Any] = {}
    if place:
        args["location"] = place
    elif lat is not None and lon is not None:
        args["lat"] = lat
        args["lon"] = lon
    else:
        args["location"] = "Washington, DC"
    return run_sync_safe(bridge.query_mcp_tool("get_weather", args))


def gev_get_weather_map(
    map_type: str = "radar",
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch precipitation radar or cloud satellite imagery overlay for a region."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "United States"}
    return run_sync_safe(bridge.query_mcp_tool("get_weather_map", {"map_type": map_type, "area": area}))


def gev_fetch_firms_hotspots(
    bbox: list[float] | None = None,
    min_frp: float = 0.0,
    source: str = "VIIRS_NOAA20",
    days: int = 1,
) -> list[dict[str, Any]]:
    """Fetch NASA FIRMS thermal hotspots and active wildfire perimeters."""
    engine = resolve_gods_eye_view_engine()
    hotspots = run_sync_safe(
        engine.fetch_firms_hotspots(
            bbox=bbox,
            min_frp=min_frp,
            source=source,
            days=days,
        )
    )
    return [h.model_dump() for h in hotspots]


def gev_get_active_fires(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Fetch NASA FIRMS active thermal anomalies and fire perimeters in an area."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "California"}
    return run_sync_safe(bridge.query_mcp_tool("get_active_fires", {"area": area, "limit": limit}))


def gev_fetch_earthquakes(
    min_magnitude: float = 2.5,
    timeframe: str = "all_day",
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> list[dict[str, Any]]:
    """Query USGS live seismic telemetry."""
    engine = resolve_gods_eye_view_engine()
    quakes = run_sync_safe(
        engine.fetch_earthquakes(
            min_magnitude=min_magnitude,
            timeframe=timeframe,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
        )
    )
    return [q.model_dump() for q in quakes]


def gev_get_cyclones(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch active tropical cyclone, hurricane, and typhoon advisories."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Atlantic Basin"}
    return run_sync_safe(bridge.query_mcp_tool("get_cyclones", {"area": area}))
