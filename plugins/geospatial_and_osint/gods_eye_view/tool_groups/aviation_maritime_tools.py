"""Aviation and maritime OSINT standalone tools."""

from __future__ import annotations

from typing import Any
from ..async_runner import run_sync_safe
from ..engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge


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
        args["name"] = "EVER GIVEN"
    return run_sync_safe(bridge.query_mcp_tool("find_vessel", args))


def gev_get_vessel_track(
    mmsi: str,
) -> dict[str, Any]:
    """Fetch recent position track history for an AIS vessel."""
    bridge = resolve_node_cli_bridge()
    return run_sync_safe(bridge.query_mcp_tool("get_vessel_track", {"mmsi": mmsi}))
