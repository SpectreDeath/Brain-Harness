"""Analyst query and situational awareness standalone tools."""

from __future__ import annotations

from typing import Any
from ..async_runner import run_sync_safe
from ..engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge


def _build_area_dict(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any] | None:
    if place:
        return {"place": place}
    if bbox and len(bbox) == 4:
        return {"bbox": bbox}
    if lat is not None and lon is not None and radius_km is not None:
        return {"lat": lat, "lon": lon, "radius_km": radius_km}
    return None


def gev_analyst_query(
    layer: str,
    filters: list[dict[str, Any]] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    bbox: list[float] | None = None,
    follow_up_token: str | None = None,
) -> dict[str, Any]:
    """Execute multi-layer spatial queries, compound filters, and aggregations across flights, vessels, fires, and earthquakes."""
    engine = resolve_gods_eye_view_engine()
    res = run_sync_safe(
        engine.query_analyst(
            layer=layer,
            filters=filters,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            bbox=bbox,
            follow_up_token=follow_up_token,
        )
    )
    return res.model_dump()


def gev_situation_brief(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Generate composite multi-domain situation overview for a geographic region."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Taiwan Strait"}
    return run_sync_safe(bridge.query_mcp_tool("situation_brief", {"area": area}))
