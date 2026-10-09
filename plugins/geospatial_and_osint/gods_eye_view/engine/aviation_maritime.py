"""Live aviation and maritime telemetry fetchers with caching and fallbacks."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from ..models import FlightRecord, VesselRecord
from ..telemetry_cache import TelemetryCache
from .mock_data import MOCK_FLIGHTS, MOCK_VESSELS, asyncio_wrap

logger = structlog.get_logger(__name__)


async def raw_fetch_opensky(http_timeout: float, bbox: list[float] | None = None) -> list[FlightRecord]:
    """Low-level OpenSky Network fetcher."""
    flights: list[FlightRecord] = []
    try:
        url = "https://opensky-network.org/api/states/all"
        params: dict[str, Any] = {}
        if bbox and len(bbox) == 4:
            params["lamin"] = bbox[1]
            params["lomin"] = bbox[2]
            params["lamax"] = bbox[0]
            params["lomax"] = bbox[3]

        async with httpx.AsyncClient(timeout=http_timeout) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                states = data.get("states") or []
                for s in states:
                    if not s or len(s) < 17:
                        continue
                    hex_code = str(s[0]).lower().strip()
                    c_sign = str(s[1]).strip() if s[1] else None
                    origin_c = str(s[2]) if s[2] else "Unknown"
                    flon = float(s[5]) if s[5] is not None else None
                    flat = float(s[6]) if s[6] is not None else None
                    if flat is None or flon is None:
                        continue

                    alt = float(s[7]) if s[7] is not None else (float(s[13]) if s[13] is not None else None)
                    vel = float(s[9]) if s[9] is not None else None
                    track = float(s[10]) if s[10] is not None else None
                    v_rate = float(s[11]) if s[11] is not None else None
                    ground = bool(s[8])

                    is_mil = origin_c in ["United States", "United Kingdom", "Israel", "Germany"] and (
                        (c_sign and any(c_sign.startswith(p) for p in ["RCH", "EVAC", "SAM", "VIPER", "COBRA", "FORTE", "JAKE"]))
                        or hex_code.startswith("ae")
                    )

                    flights.append(
                        FlightRecord(
                            icao24=hex_code,
                            callsign=c_sign,
                            origin_country=origin_c,
                            lat=flat,
                            lon=flon,
                            altitude_m=alt,
                            velocity_mps=vel,
                            heading_deg=track,
                            vertical_rate_mps=v_rate,
                            on_ground=ground,
                            military=is_mil,
                        )
                    )
    except Exception as e:
        logger.debug("OpenSky live feed unavailable, fallback to mock", error=str(e))

    return flights if flights else list(MOCK_FLIGHTS)


async def fetch_flights(
    cache: TelemetryCache[Any],
    http_timeout: float,
    bbox: list[float] | None = None,
    icao24: str | None = None,
    callsign: str | None = None,
    military_only: bool = False,
    limit: int = 200,
    force_refresh: bool = False,
) -> list[FlightRecord]:
    """Fetch live flights with single-flight caching and spatial grid pruning."""
    cache_key = f"flights_{bbox}" if bbox else "flights_global"
    all_flights: list[FlightRecord] = await cache.get_or_fetch(
        cache_key,
        lambda: raw_fetch_opensky(http_timeout, bbox),
        ttl_seconds=15.0,
        force_refresh=force_refresh,
    )

    filtered = all_flights
    if military_only:
        filtered = [f for f in filtered if f.military]
    if icao24:
        filtered = [f for f in filtered if f.icao24.lower() == icao24.lower()]
    if callsign:
        cs_clean = callsign.lower()
        filtered = [f for f in filtered if f.callsign and cs_clean in f.callsign.lower()]
    if bbox and len(bbox) == 4:
        n, s, w, e = bbox
        filtered = [f for f in filtered if s <= f.lat <= n and w <= f.lon <= e]

    return filtered[:limit]


async def fetch_vessels(
    cache: TelemetryCache[Any],
    bbox: list[float] | None = None,
    mmsi: str | None = None,
    ship_type: str | None = None,
    destination: str | None = None,
    limit: int = 200,
) -> list[VesselRecord]:
    """Fetch maritime AIS vessel records with caching."""
    vessels: list[VesselRecord] = await cache.get_or_fetch(
        "vessels_global",
        lambda: asyncio_wrap(MOCK_VESSELS),
        ttl_seconds=30.0,
    )

    filtered = vessels
    if mmsi:
        filtered = [v for v in filtered if v.mmsi == mmsi]
    if ship_type:
        st_clean = ship_type.lower()
        filtered = [v for v in filtered if st_clean in v.ship_type.lower()]
    if destination:
        dst_clean = destination.lower()
        filtered = [v for v in filtered if v.destination and dst_clean in v.destination.lower()]
    if bbox and len(bbox) == 4:
        n, s, w, e = bbox
        filtered = [v for v in filtered if s <= v.lat <= n and w <= v.lon <= e]

    return filtered[:limit]


__all__ = [
    "fetch_flights",
    "fetch_vessels",
    "raw_fetch_opensky",
]
