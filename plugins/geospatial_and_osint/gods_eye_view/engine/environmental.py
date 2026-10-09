"""Live environmental and geophysical telemetry fetchers with caching and fallbacks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from ..infrastructure_store import haversine_km
from ..models import EarthquakeRecord, ThermalHotspotRecord
from ..telemetry_cache import TelemetryCache
from .mock_data import MOCK_EARTHQUAKES, MOCK_FIRMS, asyncio_wrap

logger = structlog.get_logger(__name__)


async def raw_fetch_usgs(http_timeout: float, timeframe: str) -> list[EarthquakeRecord]:
    """Low-level USGS earthquake feed fetcher."""
    quakes: list[EarthquakeRecord] = []
    try:
        feed_suffix = "all_day.geojson" if timeframe == "all_day" else "all_week.geojson"
        url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{feed_suffix}"
        async with httpx.AsyncClient(timeout=http_timeout) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for feat in data.get("features", []):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    mag = float(props.get("mag") or 0.0)
                    if len(coords) < 3:
                        continue

                    q_lon = float(coords[0])
                    q_lat = float(coords[1])
                    q_depth = float(coords[2])
                    ev_id = str(feat.get("id") or props.get("code") or uuid.uuid4().hex[:8])
                    title = str(props.get("title") or f"M {mag:.1f}")
                    place = str(props.get("place") or "Unknown Location")
                    tsunami = bool(props.get("tsunami", 0))
                    ev_url = props.get("url")
                    t_ms = props.get("time")
                    t_iso = (
                        datetime.fromtimestamp(t_ms / 1000.0, tz=timezone.utc).isoformat()
                        if t_ms
                        else datetime.now(timezone.utc).isoformat()
                    )

                    quakes.append(
                        EarthquakeRecord(
                            event_id=ev_id,
                            title=title,
                            magnitude=mag,
                            place=place,
                            lat=q_lat,
                            lon=q_lon,
                            depth_km=q_depth,
                            time_utc=t_iso,
                            tsunami_alert=tsunami,
                            url=ev_url,
                        )
                    )
    except Exception as e:
        logger.debug("USGS live feed error, fallback to mock", error=str(e))

    return quakes if quakes else list(MOCK_EARTHQUAKES)


async def fetch_earthquakes(
    cache: TelemetryCache[Any],
    http_timeout: float,
    min_magnitude: float = 2.5,
    timeframe: str = "all_day",
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    limit: int = 100,
    force_refresh: bool = False,
) -> list[EarthquakeRecord]:
    """Query USGS live earthquake feed backed by TelemetryCache."""
    cache_key = f"earthquakes_{timeframe}"
    quakes: list[EarthquakeRecord] = await cache.get_or_fetch(
        cache_key,
        lambda: raw_fetch_usgs(http_timeout, timeframe),
        ttl_seconds=60.0,
        force_refresh=force_refresh,
    )

    filtered = [q for q in quakes if q.magnitude >= min_magnitude]
    if lat is not None and lon is not None and radius_km is not None:
        filtered = [q for q in filtered if haversine_km(lat, lon, q.lat, q.lon) <= radius_km]

    return filtered[:limit]


async def fetch_firms_hotspots(
    cache: TelemetryCache[Any],
    bbox: list[float] | None = None,
    min_frp: float = 0.0,
    source: str = "VIIRS_NOAA20",
    days: int = 1,
    limit: int = 100,
) -> list[ThermalHotspotRecord]:
    """Fetch NASA FIRMS thermal hotspots with caching."""
    hotspots: list[ThermalHotspotRecord] = await cache.get_or_fetch(
        "firms_hotspots",
        lambda: asyncio_wrap(MOCK_FIRMS),
        ttl_seconds=300.0,
    )

    filtered = [h for h in hotspots if h.frp_mw >= min_frp]
    if bbox and len(bbox) == 4:
        n, s, w, e = bbox
        filtered = [h for h in filtered if s <= h.lat <= n and w <= h.lon <= e]

    return filtered[:limit]


__all__ = [
    "fetch_earthquakes",
    "fetch_firms_hotspots",
    "raw_fetch_usgs",
]
