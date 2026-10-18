"""God's Eye View service protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

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


@runtime_checkable
class GodsEyeViewService(Protocol):
    """Protocol for the God's Eye View Planetary Intelligence Service."""

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
        """Execute multi-layer spatial queries, compound filters, and aggregations."""
        ...

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
    ) -> list[FlightRecord]:
        """Fetch live aviation transponder vectors with OpenSky / ADSB-lol fallback."""
        ...

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        """Retrieve real-time maritime AIS vessel records."""
        ...

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[EarthquakeRecord]:
        """Query USGS live seismic telemetry."""
        ...

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS thermal hotspots and active wildfire perimeters."""
        ...

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        """Compute tactical military awareness corridor and air/naval assets."""
        ...

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        """Predict upcoming orbital overpasses over ground coordinates."""
        ...

    async def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[InfrastructureRecord]:
        """Query offline global submarine cables, datacenters, dams, and POIs."""
        ...

    async def render_sat_ortho(
        self,
        lat: float,
        lon: float,
        zoom: int = 21,
        size: int = 2048,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Stitch high-resolution satellite orthomosaic from 3D Map Tiles."""
        ...

    async def capture_streetview_headings(
        self,
        lat: float,
        lon: float,
        fov: int = 90,
        pitch: int = 0,
        neighbors: bool = False,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Capture 8 compass headings (360 ground view) via Static Street View."""
        ...

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
        """Render photorealistic 3D Cesium globe snapshots with post-processing shaders."""
        ...

    async def get_weather(
        self,
        place: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherResult:
        """Retrieve current weather conditions at point or named place."""
        ...

    async def get_weather_map(
        self,
        map_type: str = "radar",
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> WeatherMapResult:
        """Fetch precipitation radar or cloud satellite imagery overlay."""
        ...

    async def find_cctv_cameras(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 50,
    ) -> list[CctvCameraRecord]:
        """Search public camera installations in an area."""
        ...

    async def get_cctv_snapshot(
        self,
        camera_id: str,
    ) -> CctvSnapshotResult:
        """Retrieve latest still snapshot frame from public camera."""
        ...

    async def find_aircraft(
        self,
        callsign: str | None = None,
        icao24: str | None = None,
        registration: str | None = None,
        limit: int = 50,
    ) -> list[FlightRecord]:
        """Search aircraft globally by callsign, ICAO hex, or tail registration."""
        ...

    async def get_aircraft_track(
        self,
        icao24: str,
        military: bool = False,
    ) -> AircraftTrackRecord:
        """Fetch recent position history track for an aircraft."""
        ...

    async def find_vessel(
        self,
        mmsi: str | None = None,
        imo: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[VesselRecord]:
        """Search vessels globally by MMSI, IMO number, or vessel name."""
        ...

    async def get_vessel_track(
        self,
        mmsi: str,
    ) -> VesselTrackRecord:
        """Fetch recent position track history for an AIS vessel."""
        ...

    async def situation_brief(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> SituationBriefResult:
        """Generate composite multi-domain situation overview for an area."""
        ...

    async def get_terrain_height(
        self,
        points: list[dict[str, float]],
    ) -> list[TerrainHeightRecord]:
        """Query terrain ground elevation above sea level for coordinate points."""
        ...

    async def get_cyclones(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[CycloneRecord]:
        """Fetch active tropical cyclone and hurricane advisories."""
        ...

    async def get_active_fires(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS active fires in an area."""
        ...

    async def get_recent_imagery(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> dict[str, Any]:
        """Fetch recent Landsat/Sentinel/VIIRS optical satellite imagery metadata."""
        ...


__all__ = ["GodsEyeViewService"]
