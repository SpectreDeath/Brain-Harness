"""Resolver and Rule 58 adapter seam for God's Eye View service."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal
import structlog

from harness.kernel.context import ServiceContext
from .keys import GODS_EYE_VIEW_SERVICE_KEY
from .models import (
    AircraftTrackRecord,
    AnalystQueryResult,
    CctvCameraRecord,
    CctvSnapshotResult,
    CycloneRecord,
    EarthquakeRecord,
    FlightRecord,
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
from .protocols import GodsEyeViewService

logger = structlog.get_logger(__name__)

METHOD_TO_ENTRYPOINT: dict[str, str] = {
    "query_analyst": "gev_analyst_query",
    "fetch_flights": "gev_fetch_live_flights",
    "fetch_vessels": "gev_fetch_ais_vessels",
    "fetch_earthquakes": "gev_fetch_earthquakes",
    "fetch_firms_hotspots": "gev_fetch_firms_hotspots",
    "query_military_awareness": "gev_query_military_awareness",
    "calculate_satellite_passes": "gev_calculate_satellite_passes",
    "query_infrastructure": "gev_query_infrastructure",
    "render_sat_ortho": "gev_render_sat_ortho",
    "capture_streetview_headings": "gev_capture_streetview_headings",
    "render_globe_snapshot": "gev_render_globe_snapshot",
    "get_weather": "gev_get_weather",
    "get_weather_map": "gev_get_weather_map",
    "find_cctv_cameras": "gev_find_cctv_cameras",
    "get_cctv_snapshot": "gev_get_cctv_snapshot",
    "find_aircraft": "gev_find_aircraft",
    "get_aircraft_track": "gev_get_aircraft_track",
    "find_vessel": "gev_find_vessel",
    "get_vessel_track": "gev_get_vessel_track",
    "situation_brief": "gev_situation_brief",
    "get_terrain_height": "gev_get_terrain_height",
    "get_cyclones": "gev_get_cyclones",
    "get_active_fires": "gev_get_active_fires",
    "get_recent_imagery": "gev_get_recent_imagery",
}


def attach_provenance_envelope(
    data: Any,
    source_mode: Literal["live", "cached", "simulated_fallback"] = "live",
    ttl_seconds: float = 30.0,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    """Wrap output dictionary with explicit provenance and freshness metadata."""
    now_utc = datetime.now(timezone.utc).isoformat()
    base_data = data.model_dump() if hasattr(data, "model_dump") else (data.to_dict() if hasattr(data, "to_dict") else data)
    return {
        "status": "ok",
        "source_mode": source_mode,
        "fetched_at_utc": now_utc,
        "ttl_seconds": ttl_seconds,
        "fallback_reason": fallback_reason,
        "payload": base_data,
    }


class GodsEyeViewAdapter(GodsEyeViewService):
    """Rule 58 Adapter unifying SandboxedPlugin subprocess calls and in-process implementations."""

    def __init__(self, provider: Any) -> None:
        self._provider = provider

    def _invoke_sync(self, entrypoint: str, kwargs: dict[str, Any]) -> Any:
        if hasattr(self._provider, "invoke_typed"):
            call_res = asyncio.run(self._provider.invoke_typed(entrypoint, kwargs))
            return call_res.result if hasattr(call_res, "result") else call_res
        if hasattr(self._provider, "call"):
            return asyncio.run(self._provider.call(entrypoint, kwargs))
        raise AttributeError(f"Provider {type(self._provider)} does not support invocation for {entrypoint}")

    async def query_analyst(self, *args: Any, **kwargs: Any) -> AnalystQueryResult:
        if hasattr(self._provider, "query_analyst"):
            res = self._provider.query_analyst(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_analyst_query", kwargs)
        return AnalystQueryResult(**raw) if isinstance(raw, dict) else raw

    async def fetch_flights(self, *args: Any, **kwargs: Any) -> list[FlightRecord]:
        if hasattr(self._provider, "fetch_flights"):
            res = self._provider.fetch_flights(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_fetch_live_flights", kwargs)
        if isinstance(raw, list):
            return [FlightRecord(**f) if isinstance(f, dict) else f for f in raw]
        return []

    async def fetch_vessels(self, *args: Any, **kwargs: Any) -> list[VesselRecord]:
        if hasattr(self._provider, "fetch_vessels"):
            res = self._provider.fetch_vessels(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_fetch_ais_vessels", kwargs)
        if isinstance(raw, list):
            return [VesselRecord(**v) if isinstance(v, dict) else v for v in raw]
        return []

    async def fetch_earthquakes(self, *args: Any, **kwargs: Any) -> list[EarthquakeRecord]:
        if hasattr(self._provider, "fetch_earthquakes"):
            res = self._provider.fetch_earthquakes(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_fetch_earthquakes", kwargs)
        if isinstance(raw, list):
            return [EarthquakeRecord(**e) if isinstance(e, dict) else e for e in raw]
        return []

    async def fetch_firms_hotspots(self, *args: Any, **kwargs: Any) -> list[ThermalHotspotRecord]:
        if hasattr(self._provider, "fetch_firms_hotspots"):
            res = self._provider.fetch_firms_hotspots(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_fetch_firms_hotspots", kwargs)
        if isinstance(raw, list):
            return [ThermalHotspotRecord(**h) if isinstance(h, dict) else h for h in raw]
        return []

    async def query_military_awareness(self, *args: Any, **kwargs: Any) -> MilitaryAwarenessSummary:
        if hasattr(self._provider, "query_military_awareness"):
            res = self._provider.query_military_awareness(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_query_military_awareness", kwargs)
        return MilitaryAwarenessSummary(**raw) if isinstance(raw, dict) else raw

    async def calculate_satellite_passes(self, *args: Any, **kwargs: Any) -> list[SatellitePassRecord]:
        if hasattr(self._provider, "calculate_satellite_passes"):
            res = self._provider.calculate_satellite_passes(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_calculate_satellite_passes", kwargs)
        if isinstance(raw, list):
            return [SatellitePassRecord(**s) if isinstance(s, dict) else s for s in raw]
        return []

    async def query_infrastructure(self, *args: Any, **kwargs: Any) -> list[InfrastructureRecord]:
        if hasattr(self._provider, "query_infrastructure"):
            res = self._provider.query_infrastructure(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_query_infrastructure", kwargs)
        if isinstance(raw, list):
            return [InfrastructureRecord(**i) if isinstance(i, dict) else i for i in raw]
        return []

    async def render_sat_ortho(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        if hasattr(self._provider, "render_sat_ortho"):
            res = self._provider.render_sat_ortho(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_render_sat_ortho", kwargs)
        return ImageryRenderResult(**raw) if isinstance(raw, dict) else raw

    async def capture_streetview_headings(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        if hasattr(self._provider, "capture_streetview_headings"):
            res = self._provider.capture_streetview_headings(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_capture_streetview_headings", kwargs)
        return ImageryRenderResult(**raw) if isinstance(raw, dict) else raw

    async def render_globe_snapshot(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        if hasattr(self._provider, "render_globe_snapshot"):
            res = self._provider.render_globe_snapshot(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_render_globe_snapshot", kwargs)
        return ImageryRenderResult(**raw) if isinstance(raw, dict) else raw

    async def get_weather(self, *args: Any, **kwargs: Any) -> WeatherResult:
        if hasattr(self._provider, "get_weather"):
            res = self._provider.get_weather(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_weather", kwargs)
        return WeatherResult(**raw) if isinstance(raw, dict) else raw

    async def get_weather_map(self, *args: Any, **kwargs: Any) -> WeatherMapResult:
        if hasattr(self._provider, "get_weather_map"):
            res = self._provider.get_weather_map(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_weather_map", kwargs)
        return WeatherMapResult(**raw) if isinstance(raw, dict) else raw

    async def find_cctv_cameras(self, *args: Any, **kwargs: Any) -> list[CctvCameraRecord]:
        if hasattr(self._provider, "find_cctv_cameras"):
            res = self._provider.find_cctv_cameras(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_find_cctv_cameras", kwargs)
        if isinstance(raw, list):
            return [CctvCameraRecord(**c) if isinstance(c, dict) else c for c in raw]
        return []

    async def get_cctv_snapshot(self, *args: Any, **kwargs: Any) -> CctvSnapshotResult:
        if hasattr(self._provider, "get_cctv_snapshot"):
            res = self._provider.get_cctv_snapshot(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_cctv_snapshot", kwargs)
        return CctvSnapshotResult(**raw) if isinstance(raw, dict) else raw

    async def find_aircraft(self, *args: Any, **kwargs: Any) -> list[FlightRecord]:
        if hasattr(self._provider, "find_aircraft"):
            res = self._provider.find_aircraft(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_find_aircraft", kwargs)
        if isinstance(raw, list):
            return [FlightRecord(**f) if isinstance(f, dict) else f for f in raw]
        return []

    async def get_aircraft_track(self, *args: Any, **kwargs: Any) -> AircraftTrackRecord:
        if hasattr(self._provider, "get_aircraft_track"):
            res = self._provider.get_aircraft_track(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_aircraft_track", kwargs)
        return AircraftTrackRecord(**raw) if isinstance(raw, dict) else raw

    async def find_vessel(self, *args: Any, **kwargs: Any) -> list[VesselRecord]:
        if hasattr(self._provider, "find_vessel"):
            res = self._provider.find_vessel(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_find_vessel", kwargs)
        if isinstance(raw, list):
            return [VesselRecord(**v) if isinstance(v, dict) else v for v in raw]
        return []

    async def get_vessel_track(self, *args: Any, **kwargs: Any) -> VesselTrackRecord:
        if hasattr(self._provider, "get_vessel_track"):
            res = self._provider.get_vessel_track(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_vessel_track", kwargs)
        return VesselTrackRecord(**raw) if isinstance(raw, dict) else raw

    async def situation_brief(self, *args: Any, **kwargs: Any) -> SituationBriefResult:
        if hasattr(self._provider, "situation_brief"):
            res = self._provider.situation_brief(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_situation_brief", kwargs)
        return SituationBriefResult(**raw) if isinstance(raw, dict) else raw

    async def get_terrain_height(self, *args: Any, **kwargs: Any) -> list[TerrainHeightRecord]:
        if hasattr(self._provider, "get_terrain_height"):
            res = self._provider.get_terrain_height(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_terrain_height", kwargs)
        if isinstance(raw, list):
            return [TerrainHeightRecord(**t) if isinstance(t, dict) else t for t in raw]
        return []

    async def get_cyclones(self, *args: Any, **kwargs: Any) -> list[CycloneRecord]:
        if hasattr(self._provider, "get_cyclones"):
            res = self._provider.get_cyclones(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_cyclones", kwargs)
        if isinstance(raw, list):
            return [CycloneRecord(**c) if isinstance(c, dict) else c for c in raw]
        return []

    async def get_active_fires(self, *args: Any, **kwargs: Any) -> list[ThermalHotspotRecord]:
        if hasattr(self._provider, "get_active_fires"):
            res = self._provider.get_active_fires(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_active_fires", kwargs)
        if isinstance(raw, list):
            return [ThermalHotspotRecord(**f) if isinstance(f, dict) else f for f in raw]
        return []

    async def get_recent_imagery(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        if hasattr(self._provider, "get_recent_imagery"):
            res = self._provider.get_recent_imagery(*args, **kwargs)
            return await res if asyncio.iscoroutine(res) else res
        raw = self._invoke_sync("gev_get_recent_imagery", kwargs)
        return raw if isinstance(raw, dict) else {"status": "ok", "result": raw}


def resolve_gods_eye_view(ctx: ServiceContext | None = None) -> GodsEyeViewService:
    """Resolve authoritative GodsEyeViewService adhering to Rule 58 dual-mode adaptation."""
    if ctx and ctx.has(GODS_EYE_VIEW_SERVICE_KEY):
        provider = ctx.require(GODS_EYE_VIEW_SERVICE_KEY)
        # Check if provider has all protocol methods or is a mock/sandboxed plugin
        if isinstance(provider, GodsEyeViewService):
            return provider
        return GodsEyeViewAdapter(provider)

    # In-process plugin fallback
    try:
        from plugins.geospatial_and_osint.gods_eye_view.main import plugin
        return plugin
    except Exception as e:
        logger.debug("gods_eye_view_plugin_import_fallback", error=str(e))
        from plugins.geospatial_and_osint.gods_eye_view.main import GodsEyeViewPlugin
        return GodsEyeViewPlugin()

