"""God's Eye View planetary intelligence and OSINT analytics plugin entrypoint.

Exposes GodsEyeViewPlugin registering GODS_EYE_VIEW_SERVICE_KEY into IoC container
and re-exports all 24 standalone CLI tool entrypoints for full backward compatibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.gods_eye_view import (
    GODS_EYE_VIEW_SERVICE_KEY,
    AnalystQueryResult,
    EarthquakeRecord,
    FlightRecord,
    GodsEyeViewService,
    ImageryRenderResult,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    SatellitePassRecord,
    ThermalHotspotRecord,
    VesselRecord,
)
from .adapters import Tier2AdapterMixin
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


class GodsEyeViewPlugin(HarnessPlugin, Tier2AdapterMixin, GodsEyeViewService):
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

    # Core Engine Method Forwarders
    async def query_analyst(self, *args: Any, **kwargs: Any) -> AnalystQueryResult:
        return await self._engine.query_analyst(*args, **kwargs)

    async def fetch_flights(self, *args: Any, **kwargs: Any) -> list[FlightRecord]:
        return await self._engine.fetch_flights(*args, **kwargs)

    async def fetch_vessels(self, *args: Any, **kwargs: Any) -> list[VesselRecord]:
        return await self._engine.fetch_vessels(*args, **kwargs)

    async def fetch_earthquakes(self, *args: Any, **kwargs: Any) -> list[EarthquakeRecord]:
        return await self._engine.fetch_earthquakes(*args, **kwargs)

    async def fetch_firms_hotspots(self, *args: Any, **kwargs: Any) -> list[ThermalHotspotRecord]:
        return await self._engine.fetch_firms_hotspots(*args, **kwargs)

    async def query_military_awareness(self, *args: Any, **kwargs: Any) -> MilitaryAwarenessSummary:
        return await self._engine.query_military_awareness(*args, **kwargs)

    async def calculate_satellite_passes(self, *args: Any, **kwargs: Any) -> list[SatellitePassRecord]:
        return await self._engine.calculate_satellite_passes(*args, **kwargs)

    async def query_infrastructure(self, *args: Any, **kwargs: Any) -> list[InfrastructureRecord]:
        return self._engine.query_infrastructure(*args, **kwargs)

    async def render_sat_ortho(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        return await self._engine.render_sat_ortho(*args, **kwargs)

    async def capture_streetview_headings(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        return await self._engine.capture_streetview_headings(*args, **kwargs)

    async def render_globe_snapshot(self, *args: Any, **kwargs: Any) -> ImageryRenderResult:
        return await self._engine.render_globe_snapshot(*args, **kwargs)


plugin = GodsEyeViewPlugin()

__all__ = [
    "GodsEyeViewPlugin",
    "plugin",
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
