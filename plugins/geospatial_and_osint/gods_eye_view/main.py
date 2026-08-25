"""God's Eye View Plugin & HarnessPlugin Service Implementation."""

from __future__ import annotations

import asyncio
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.gods_eye_view import (
    AnalystQueryResult,
    EarthquakeRecord,
    FlightRecord,
    GODS_EYE_VIEW_SERVICE_KEY,
    GodsEyeViewService,
    ImageryRenderResult,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    SatellitePassRecord,
    ThermalHotspotRecord,
    VesselRecord,
)

from .cli_bridge import NodeCliBridge
from .engine import GodsEyeViewEngine

logger = structlog.get_logger(__name__)

# Global instances for standalone tool execution
_ENGINE_INSTANCE = GodsEyeViewEngine()
_BRIDGE_INSTANCE = NodeCliBridge()


def _get_engine() -> GodsEyeViewEngine:
    return _ENGINE_INSTANCE


def _get_bridge() -> NodeCliBridge:
    return _BRIDGE_INSTANCE


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
    engine = _get_engine()
    res = asyncio.run(
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
    engine = _get_engine()
    flights = asyncio.run(
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
    engine = _get_engine()
    vessels = asyncio.run(
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
    engine = _get_engine()
    quakes = asyncio.run(
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
    engine = _get_engine()
    hotspots = asyncio.run(
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
    engine = _get_engine()
    summary = asyncio.run(
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
    engine = _get_engine()
    passes = asyncio.run(
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
    engine = _get_engine()
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
    bridge = _get_bridge()
    res = asyncio.run(
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
    bridge = _get_bridge()
    res = asyncio.run(
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
    bridge = _get_bridge()
    res = asyncio.run(
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


class GodsEyeViewPlugin(HarnessPlugin, GodsEyeViewService):
    """Harness Plugin implementing GodsEyeViewService and registering GODS_EYE_VIEW_SERVICE_KEY."""

    name = "plugin.gods_eye_view"
    version = "0.1.0"
    description = "Planetary intelligence, real-time OSINT feeds, spatial analytics engine, and 3D globe rendering"
    trusted = True

    def __init__(self) -> None:
        self._engine = _get_engine()
        self._bridge = _get_bridge()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GODS_EYE_VIEW_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(GODS_EYE_VIEW_SERVICE_KEY, self)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # GodsEyeViewService Protocol Implementation
    async def query_analyst(
        self,
        layer: str,
        filters: list[dict[str, Any]] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        follow_up_token: str | None = None,
    ) -> AnalystQueryResult:
        return await self._engine.query_analyst(
            layer=layer,
            filters=filters,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            bbox=bbox,
            follow_up_token=follow_up_token,
        )

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
    ) -> list[FlightRecord]:
        return await self._engine.fetch_flights(
            bbox=bbox,
            icao24=icao24,
            callsign=callsign,
            military_only=military_only,
            limit=limit,
        )

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        return await self._engine.fetch_vessels(
            bbox=bbox,
            mmsi=mmsi,
            ship_type=ship_type,
            destination=destination,
            limit=limit,
        )

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[EarthquakeRecord]:
        return await self._engine.fetch_earthquakes(
            min_magnitude=min_magnitude,
            timeframe=timeframe,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
        )

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
    ) -> list[ThermalHotspotRecord]:
        return await self._engine.fetch_firms_hotspots(
            bbox=bbox,
            min_frp=min_frp,
            source=source,
            days=days,
        )

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        return await self._engine.query_military_awareness(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            include_bases=include_bases,
        )

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        return await self._engine.calculate_satellite_passes(
            lat=lat,
            lon=lon,
            sat_name=sat_name,
            norad_id=norad_id,
            horizon_hours=horizon_hours,
        )

    async def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[InfrastructureRecord]:
        return self._engine.query_infrastructure(
            infra_type=infra_type,
            query=query,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
        )

    async def render_sat_ortho(
        self,
        lat: float,
        lon: float,
        zoom: int = 21,
        size: int = 2048,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        return await self._bridge.render_sat_ortho(
            lat=lat,
            lon=lon,
            zoom=zoom,
            size=size,
            outdir=outdir,
        )

    async def capture_streetview_headings(
        self,
        lat: float,
        lon: float,
        fov: int = 90,
        pitch: int = 0,
        neighbors: bool = False,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        return await self._bridge.capture_streetview_headings(
            lat=lat,
            lon=lon,
            fov=fov,
            pitch=pitch,
            neighbors=neighbors,
            outdir=outdir,
        )

    async def render_globe_snapshot(
        self,
        lat: float,
        lon: float,
        altitude_m: float = 1000.0,
        pitch: float = -45.0,
        heading: float = 0.0,
        style: str = "normal",
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        return await self._bridge.render_globe_snapshot(
            lat=lat,
            lon=lon,
            altitude_m=altitude_m,
            pitch=pitch,
            heading=heading,
            style=style,
            outdir=outdir,
        )
