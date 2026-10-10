"""God's Eye View planetary intelligence and OSINT analytics plugin entrypoint.

Exposes GodsEyeViewPlugin registering GODS_EYE_VIEW_SERVICE_KEY into IoC container
and re-exports all 24 standalone CLI tool entrypoints for full backward compatibility.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog
import yaml

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.gods_eye_view import (
    GODS_EYE_VIEW_SERVICE_KEY,
    AircraftTrackRecord,
    AnalystQueryResult,
    CctvCameraRecord,
    CctvSnapshotResult,
    CycloneRecord,
    EarthquakeRecord,
    FlightRecord,
    GodsEyeViewService,
    ImageryRenderResult,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    SatellitePassRecord,
    SituationBriefResult,
    TerrainHeightRecord,
    ThermalHotspotRecord,
    VesselRecord,
    VesselTrackRecord,
    WeatherMapResult,
    WeatherResult,
)
from .engine.resolvers import resolve_gods_eye_view_engine, resolve_node_cli_bridge
from .tools import (
    _build_area_dict,
    gev_analyst_query,
    gev_calculate_satellite_passes,
    gev_capture_streetview_headings,
    gev_fetch_ais_vessels,
    gev_fetch_earthquakes,
    gev_fetch_firms_hotspots,
    gev_fetch_live_flights,
    gev_find_aircraft,
    gev_find_cctv_cameras,
    gev_find_vessel,
    gev_get_active_fires,
    gev_get_aircraft_track,
    gev_get_cctv_snapshot,
    gev_get_cyclones,
    gev_get_recent_imagery,
    gev_get_terrain_height,
    gev_get_vessel_track,
    gev_get_weather,
    gev_get_weather_map,
    gev_query_infrastructure,
    gev_query_military_awareness,
    gev_render_globe_snapshot,
    gev_render_sat_ortho,
    gev_situation_brief,
)

logger = structlog.get_logger(__name__)


def _get_engine():
    return resolve_gods_eye_view_engine()


def _get_bridge():
    return resolve_node_cli_bridge()


class GodsEyeViewPlugin(HarnessPlugin, GodsEyeViewService):
    """Harness Plugin implementing GodsEyeViewService and registering GODS_EYE_VIEW_SERVICE_KEY."""

    name = "plugin.gods_eye_view"
    version = "0.1.0"

    def __init__(self, data_dir: str | None = None) -> None:
        super().__init__()
        self._engine = resolve_gods_eye_view_engine(data_dir=data_dir)
        self._bridge = resolve_node_cli_bridge()
        self.config: dict[str, Any] = {}

    @property
    def provides(self) -> list[Any]:
        return [GODS_EYE_VIEW_SERVICE_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        config_path = Path(__file__).parent / "config.default.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("config_load_error", error=str(e))
                self.config = {}
        else:
            self.config = {}
        ctx.provide(GODS_EYE_VIEW_SERVICE_KEY, self)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # Helper for structured MCP responses
    async def _query_mcp(self, tool_name: str, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        resp = await self._bridge.query_mcp_tool(tool_name, args)
        data = resp.get("result", {}).get("structuredContent", resp)
        return data, resp

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
            layer=layer, filters=filters, lat=lat, lon=lon,
            radius_km=radius_km, bbox=bbox, follow_up_token=follow_up_token,
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
            bbox=bbox, icao24=icao24, callsign=callsign,
            military_only=military_only, limit=limit,
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
            bbox=bbox, mmsi=mmsi, ship_type=ship_type,
            destination=destination, limit=limit,
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
            min_magnitude=min_magnitude, timeframe=timeframe,
            lat=lat, lon=lon, radius_km=radius_km,
        )

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
    ) -> list[ThermalHotspotRecord]:
        return await self._engine.fetch_firms_hotspots(
            bbox=bbox, min_frp=min_frp, source=source, days=days,
        )

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        return await self._engine.query_military_awareness(
            lat=lat, lon=lon, radius_km=radius_km, include_bases=include_bases,
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
            lat=lat, lon=lon, sat_name=sat_name, norad_id=norad_id, horizon_hours=horizon_hours,
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
            infra_type=infra_type, query=query, lat=lat, lon=lon, radius_km=radius_km,
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
            lat=lat, lon=lon, zoom=zoom, size=size, outdir=outdir,
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
            lat=lat, lon=lon, fov=fov, pitch=pitch, neighbors=neighbors, outdir=outdir,
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
            lat=lat, lon=lon, altitude_m=altitude_m, pitch=pitch,
            heading=heading, style=style, outdir=outdir,
        )

    # Tier 2 Pass-Through Methods
    async def get_weather(
        self,
        place: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherResult:
        loc = {"place": place} if place else {"lat": lat or 0.0, "lon": lon or 0.0}
        data, meta = await self._query_mcp("get_weather", {"location": loc})
        return WeatherResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            location=data.get("location", loc),
            weather=data.get("weather", {}),
            summary=meta.get("summary", ""),
        )

    async def get_weather_map(
        self,
        map_type: str = "radar",
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> WeatherMapResult:
        args: dict[str, Any] = {"map": map_type}
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km)
        if area:
            args["area"] = area
        data, meta = await self._query_mcp("get_weather_map", args)
        return WeatherMapResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            map_type=data.get("map", map_type),
            summary=meta.get("summary", ""),
            image_url_or_b64=data.get("image"),
        )

    async def find_cctv_cameras(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 50,
    ) -> list[CctvCameraRecord]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Downtown"}
        data, _ = await self._query_mcp("find_cctv_cameras", {"area": area, "limit": limit})
        rows = data.get("rows", [])
        return [
            CctvCameraRecord(
                id=r.get("id", "cctv_01"),
                camera_id=r.get("id", "cctv_01"),
                name=r.get("name", "Traffic Camera"),
                city=r.get("city"),
                provider=r.get("provider"),
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                distance_km=r.get("distance_km"),
            )
            for r in rows
        ]

    async def get_cctv_snapshot(self, camera_id: str) -> CctvSnapshotResult:
        data, meta = await self._query_mcp("get_cctv_snapshot", {"camera_id": camera_id})
        return CctvSnapshotResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            camera_id=camera_id,
            summary=meta.get("summary", ""),
            image_url_or_b64=data.get("image"),
        )

    async def find_aircraft(
        self,
        callsign: str | None = None,
        icao24: str | None = None,
        registration: str | None = None,
        limit: int = 50,
    ) -> list[FlightRecord]:
        args: dict[str, Any] = {"limit": limit}
        if callsign:
            args["callsign"] = callsign
        elif icao24:
            args["icao24"] = icao24
        elif registration:
            args["registration"] = registration
        else:
            args["callsign"] = "AF1"
        data, _ = await self._query_mcp("find_aircraft", args)
        rows = data.get("rows", [])
        return [
            FlightRecord(
                icao24=r.get("id") or r.get("icao24", "ae0001"),
                callsign=r.get("callsign"),
                origin_country=r.get("origin_country", "Unknown"),
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                altitude_m=r.get("altitude_m"),
                velocity_mps=r.get("speed_mps"),
                heading_deg=r.get("course_deg"),
                vertical_rate_mps=r.get("vertical_rate_mps"),
                on_ground=r.get("on_ground", False),
                military=r.get("military", False),
                operator=r.get("operator"),
            )
            for r in rows
        ]

    async def get_aircraft_track(self, icao24: str, military: bool = False) -> AircraftTrackRecord:
        data, meta = await self._query_mcp("get_aircraft_track", {"icao24": icao24, "military": military})
        points = data.get("points", [])
        return AircraftTrackRecord(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            icao24=icao24,
            callsign=data.get("callsign"),
            points=points,
            total_points=data.get("total", len(points)),
            summary=meta.get("summary", ""),
        )

    async def find_vessel(
        self,
        mmsi: str | None = None,
        imo: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[VesselRecord]:
        args: dict[str, Any] = {"limit": limit}
        if mmsi:
            args["mmsi"] = mmsi
        elif imo:
            args["imo"] = imo
        elif name:
            args["name"] = name
        else:
            args["name"] = "CARGO"
        data, _ = await self._query_mcp("find_vessel", args)
        rows = data.get("rows", [])
        return [
            VesselRecord(
                mmsi=r.get("mmsi", "367000000"),
                name=r.get("name", "VESSEL"),
                ship_type=r.get("ship_type", "Cargo"),
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                speed_kts=r.get("speed_kts", 0.0),
                heading_deg=r.get("course_deg"),
                destination=r.get("destination"),
                country=r.get("country"),
                length_m=r.get("length_m"),
                width_m=r.get("width_m"),
            )
            for r in rows
        ]

    async def get_vessel_track(self, mmsi: str) -> VesselTrackRecord:
        data, meta = await self._query_mcp("get_vessel_track", {"mmsi": mmsi})
        points = data.get("points", [])
        return VesselTrackRecord(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            mmsi=mmsi,
            points=points,
            total_points=data.get("total", len(points)),
            summary=meta.get("summary", ""),
        )

    async def situation_brief(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> SituationBriefResult:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Sector"}
        data, meta = await self._query_mcp("situation_brief", {"area": area})
        return SituationBriefResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            area_label=data.get("area_label", place or "Sector"),
            summary_lines=data.get("summary_lines", []),
            sections=data.get("sections", {}),
        )

    async def get_terrain_height(self, points: list[dict[str, float]]) -> list[TerrainHeightRecord]:
        data, _ = await self._query_mcp("get_terrain_height", {"points": points})
        rows = data.get("rows", [])
        return [
            TerrainHeightRecord(
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                elevation_m=r.get("elevation_m", 0.0),
            )
            for r in rows
        ]

    async def get_cyclones(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[CycloneRecord]:
        args: dict[str, Any] = {}
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km)
        if area:
            args["area"] = area
        data, _ = await self._query_mcp("get_cyclones", args)
        storms = data.get("storms", [])
        return [
            CycloneRecord(
                cyclone_id=s.get("id", "AL00"),
                name=s.get("name", "TROPICAL CYCLONE"),
                classification=s.get("classification"),
                basin=s.get("basin"),
                lat=s.get("lat", 0.0),
                lon=s.get("lon", 0.0),
                wind_speed_kts=s.get("wind_kt"),
                pressure_hpa=s.get("pressure_hpa"),
            )
            for s in storms
        ]

    async def get_active_fires(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "California"}
        data, _ = await self._query_mcp("get_active_fires", {"area": area, "limit": limit})
        rows = data.get("rows", [])
        return [
            ThermalHotspotRecord(
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                frp_mw=r.get("frp_mw", 0.0),
                confidence=r.get("confidence", "nominal"),
                brightness_k=r.get("brightness_k", 300.0),
                acq_date=r.get("acq_date"),
                satellite="SIMULATED" if "sim" in r.get("id", "") else "NOAA-20",
                instrument="VIIRS",
            )
            for r in rows
        ]

    async def get_recent_imagery(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> dict[str, Any]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Gibraltar"}
        data, meta = await self._query_mcp("get_recent_imagery", {"area": area})
        return {
            "status": meta.get("status", "ok"),
            "source": meta.get("source", "mcp_live"),
            "is_live": meta.get("is_live", True),
            "summary": meta.get("summary", ""),
            "satellite": data.get("satellite"),
            "product": data.get("product"),
            "quality": data.get("quality"),
            "cloud_pct": data.get("cloud_pct"),
            "acquisition_date": data.get("acquisition_date"),
        }


# Module singleton export per Rule 45
plugin = GodsEyeViewPlugin()

__all__ = [
    "GodsEyeViewPlugin",
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
    "plugin",
]
