"""Core GodsEyeViewEngine coordinator class delegating to specialized domain engines."""

from __future__ import annotations

from typing import Any

from ..infrastructure_store import InfrastructureStore
from ..models import (
    AnalystQueryResult,
    EarthquakeRecord,
    FlightRecord,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    SatellitePassRecord,
    ThermalHotspotRecord,
    VesselRecord,
)
from ..query_pipeline import QuerySessionStore
from ..telemetry_cache import TelemetryCache
from .analyst import execute_analyst_query
from .aviation_maritime import fetch_flights as _fetch_flights
from .aviation_maritime import fetch_vessels as _fetch_vessels
from .environmental import fetch_earthquakes as _fetch_earthquakes
from .environmental import fetch_firms_hotspots as _fetch_firms_hotspots
from .tactical import (
    calculate_satellite_passes as _calculate_satellite_passes,
    query_military_awareness as _query_military_awareness,
)


class GodsEyeViewEngine:
    """Stateful geospatial intelligence and multi-layer query coordinator engine."""

    def __init__(self, data_dir: str | None = None) -> None:
        self.infra_store = InfrastructureStore(external_data_dir=data_dir)
        self.cache: TelemetryCache[Any] = TelemetryCache()
        self.session_store = QuerySessionStore()
        self.http_timeout = 8.0

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
        force_refresh: bool = False,
    ) -> list[FlightRecord]:
        """Fetch live flights with single-flight caching and spatial grid pruning."""
        return await _fetch_flights(
            self.cache, self.http_timeout, bbox=bbox, icao24=icao24,
            callsign=callsign, military_only=military_only, limit=limit,
            force_refresh=force_refresh,
        )

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        """Fetch maritime AIS vessel records with caching."""
        return await _fetch_vessels(
            self.cache, bbox=bbox, mmsi=mmsi, ship_type=ship_type,
            destination=destination, limit=limit,
        )

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
        force_refresh: bool = False,
    ) -> list[EarthquakeRecord]:
        """Query USGS live earthquake feed backed by TelemetryCache."""
        return await _fetch_earthquakes(
            self.cache, self.http_timeout, min_magnitude=min_magnitude,
            timeframe=timeframe, lat=lat, lon=lon, radius_km=radius_km,
            limit=limit, force_refresh=force_refresh,
        )

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS thermal hotspots with caching."""
        return await _fetch_firms_hotspots(
            self.cache, bbox=bbox, min_frp=min_frp, source=source,
            days=days, limit=limit,
        )

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        """Analyze military contacts and base proximity in a tactical corridor."""
        return await _query_military_awareness(
            self, lat=lat, lon=lon, radius_km=radius_km, include_bases=include_bases,
        )

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        """Compute upcoming satellite overpasses over ground coordinates."""
        return await _calculate_satellite_passes(
            lat=lat, lon=lon, sat_name=sat_name, norad_id=norad_id,
            horizon_hours=horizon_hours,
        )

    def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[InfrastructureRecord]:
        """Query critical infrastructure assets with SpatialHashGrid acceleration."""
        return self.infra_store.query(
            infra_type=infra_type, search_query=query, lat=lat, lon=lon,
            radius_km=radius_km, limit=limit,
        )

    async def query_analyst(
        self,
        layer: str,
        filters: list[dict[str, Any]] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        polygon: list[tuple[float, float]] | None = None,
        follow_up_token: str | None = None,
        include_geojson: bool = True,
    ) -> AnalystQueryResult:
        """Execute multi-layer spatial query pipeline with session memory and GeoJSON export."""
        return await execute_analyst_query(
            self, layer=layer, filters=filters, lat=lat, lon=lon,
            radius_km=radius_km, bbox=bbox, polygon=polygon,
            follow_up_token=follow_up_token, include_geojson=include_geojson,
        )


__all__ = [
    "GodsEyeViewEngine",
]
