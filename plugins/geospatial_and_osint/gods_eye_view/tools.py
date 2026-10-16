"""Standalone CLI tool entrypoints for the God's Eye View geospatial intelligence plugin."""

from __future__ import annotations

from typing import Any

from .async_runner import run_sync_safe
from .engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge


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


def gev_fetch_live_flights(
    bbox: list[float] | None = None,
    icao24: str | None = None,
    callsign: str | None = None,
    military_only: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Fetch live aviation transponder vectors with OpenSky / ADSB-lol fallback."""
    engine = resolve_gods_eye_view_engine()
    flights = run_sync_safe(
        engine.fetch_flights(
            bbox=bbox,
            icao24=icao24,
            callsign=callsign,
            military_only=military_only,
            limit=limit,
        )
    )
    return [f.model_dump() for f in flights]


def gev_fetch_ais_vessels(
    bbox: list[float] | None = None,
    mmsi: str | None = None,
    ship_type: str | None = None,
    destination: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Retrieve real-time maritime AIS vessel records."""
    engine = resolve_gods_eye_view_engine()
    vessels = run_sync_safe(
        engine.fetch_vessels(
            bbox=bbox,
            mmsi=mmsi,
            ship_type=ship_type,
            destination=destination,
            limit=limit,
        )
    )
    return [v.model_dump() for v in vessels]


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


def gev_query_infrastructure(
    infra_type: str,
    query: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> list[dict[str, Any]]:
    """Query offline global submarine cables, datacenters, dams, and POIs."""
    engine = resolve_gods_eye_view_engine()
    records = engine.query_infrastructure(
        infra_type=infra_type,
        query=query,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )
    return [r.model_dump() for r in records]


def gev_render_sat_ortho(
    lat: float,
    lon: float,
    zoom: int = 21,
    size: int = 2048,
    outdir: str | None = None,
) -> dict[str, Any]:
    """Stitch high-resolution satellite orthomosaic from 3D Map Tiles."""
    bridge = resolve_node_cli_bridge()
    res = run_sync_safe(
        bridge.render_sat_ortho(
            lat=lat,
            lon=lon,
            zoom=zoom,
            size=size,
            outdir=outdir,
        )
    )
    return res.model_dump()


def gev_capture_streetview_headings(
    lat: float,
    lon: float,
    fov: int = 90,
    pitch: int = 0,
    neighbors: bool = False,
    outdir: str | None = None,
) -> dict[str, Any]:
    """Capture 8 compass headings (360 ground view) via Static Street View."""
    bridge = resolve_node_cli_bridge()
    res = run_sync_safe(
        bridge.capture_streetview_headings(
            lat=lat,
            lon=lon,
            fov=fov,
            pitch=pitch,
            neighbors=neighbors,
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
    bridge = resolve_node_cli_bridge()
    res = run_sync_safe(
        bridge.render_globe_snapshot(
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


def gev_get_weather(
    place: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any]:
    """Retrieve current weather conditions at point or named place."""
    bridge = resolve_node_cli_bridge()
    loc = {"place": place} if place else {"lat": lat or 0.0, "lon": lon or 0.0}
    return run_sync_safe(bridge.query_mcp_tool("get_weather", {"location": loc}))


def gev_get_weather_map(
    map_type: str = "radar",
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch precipitation radar or cloud satellite imagery overlay."""
    bridge = resolve_node_cli_bridge()
    args: dict[str, Any] = {"map": map_type}
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km)
    if area:
        args["area"] = area
    return run_sync_safe(bridge.query_mcp_tool("get_weather_map", args))


def gev_find_cctv_cameras(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search public camera installations in an area."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Downtown"}
    return run_sync_safe(bridge.query_mcp_tool("find_cctv_cameras", {"area": area, "limit": limit}))


def gev_get_cctv_snapshot(
    camera_id: str,
) -> dict[str, Any]:
    """Retrieve latest still snapshot frame from public camera."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_cctv_snapshot", {"camera_id": camera_id}))


def gev_find_aircraft(
    callsign: str | None = None,
    icao24: str | None = None,
    registration: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search aircraft globally by callsign, ICAO hex, or tail registration."""
    bridge = resolve_node_cli_bridge()
    args: dict[str, Any] = {"limit": limit}
    if callsign:
        args["callsign"] = callsign
    elif icao24:
        args["icao24"] = icao24
    elif registration:
        args["registration"] = registration
    else:
        args["callsign"] = "AF1"
    return run_sync_safe(bridge.query_mcp_tool("find_aircraft", args))


def gev_get_aircraft_track(
    icao24: str,
    military: bool = False,
) -> dict[str, Any]:
    """Fetch recent position history track for an aircraft."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_aircraft_track", {"icao24": icao24, "military": military}))


def gev_find_vessel(
    mmsi: str | None = None,
    imo: str | None = None,
    name: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search vessels globally by MMSI, IMO number, or vessel name."""
    bridge = resolve_node_cli_bridge()
    args: dict[str, Any] = {"limit": limit}
    if mmsi:
        args["mmsi"] = mmsi
    elif imo:
        args["imo"] = imo
    elif name:
        args["name"] = name
    else:
        args["name"] = "CARGO"
    return run_sync_safe(bridge.query_mcp_tool("find_vessel", args))


def gev_get_vessel_track(
    mmsi: str,
) -> dict[str, Any]:
    """Fetch recent position track history for an AIS vessel."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_vessel_track", {"mmsi": mmsi}))


def gev_situation_brief(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Generate composite multi-domain situation overview for an area."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Sector"}
    return run_sync_safe(bridge.query_mcp_tool("situation_brief", {"area": area}))


def gev_get_terrain_height(
    points: list[dict[str, float]],
) -> dict[str, Any]:
    """Query terrain ground elevation above sea level for coordinate points."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_terrain_height", {"points": points}))


def gev_get_cyclones(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch active tropical cyclone and hurricane advisories."""
    bridge = resolve_node_cli_bridge()
    args: dict[str, Any] = {}
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km)
    if area:
        args["area"] = area
    return run_sync_safe(bridge.query_mcp_tool("get_cyclones", args))


def gev_get_active_fires(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Fetch NASA FIRMS active fires in an area."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "California"}
    return run_sync_safe(bridge.query_mcp_tool("get_active_fires", {"area": area, "limit": limit}))


def gev_get_recent_imagery(
    place: str | None = None,
    bbox: list[float] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
) -> dict[str, Any]:
    """Fetch recent Landsat/Sentinel/VIIRS optical satellite imagery metadata."""
    bridge = resolve_node_cli_bridge()
    area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Gibraltar"}
    return run_sync_safe(bridge.query_mcp_tool("get_recent_imagery", {"area": area}))


__all__ = [
    "_build_area_dict",
    "gev_analyst_query",
    "gev_calculate_satellite_passes",
    "gev_capture_streetview_headings",
    "gev_fetch_ais_vessels",
    "gev_fetch_earthquakes",
    "gev_fetch_firms_hotspots",
    "gev_fetch_live_flights",
    "gev_find_aircraft",
    "gev_find_cctv_cameras",
    "gev_find_vessel",
    "gev_get_active_fires",
    "gev_get_aircraft_track",
    "gev_get_cctv_snapshot",
    "gev_get_cyclones",
    "gev_get_recent_imagery",
    "gev_get_terrain_height",
    "gev_get_vessel_track",
    "gev_get_weather",
    "gev_get_weather_map",
    "gev_query_infrastructure",
    "gev_query_military_awareness",
    "gev_render_globe_snapshot",
    "gev_render_sat_ortho",
    "gev_situation_brief",
]
