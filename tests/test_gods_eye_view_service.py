"""Kernel Service Registration & DI Integration tests for GodsEyeViewService."""

from __future__ import annotations

import pytest
from harness.kernel.context import ServiceContext
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


class MockGodsEyeViewService:
    """Mock implementation for testing GodsEyeViewService protocol compliance."""

    async def query_analyst(
        self,
        layer: str,
        filters: list[dict] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        follow_up_token: str | None = None,
    ) -> AnalystQueryResult:
        return AnalystQueryResult(
            status="ok",
            layer=layer,
            total_matched=1,
            items=[{"id": "mock_1", "layer": layer}],
            aggregations={"count": 1},
        )

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
    ) -> list[FlightRecord]:
        return [
            FlightRecord(
                icao24="ae1234",
                callsign="TEST01",
                origin_country="United States",
                lat=38.8951,
                lon=-77.0364,
                altitude_m=10000.0,
                velocity_mps=250.0,
                heading_deg=90.0,
                vertical_rate_mps=0.0,
                on_ground=False,
                military=military_only,
            )
        ]

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        return [
            VesselRecord(
                mmsi="367000111",
                name="TEST VESSEL",
                ship_type="Cargo",
                lat=36.93,
                lon=-76.30,
            )
        ]

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[EarthquakeRecord]:
        return [
            EarthquakeRecord(
                event_id="us_mock_1",
                title="M 5.0 - Test Location",
                magnitude=5.0,
                place="Test Location",
                lat=35.0,
                lon=-118.0,
                depth_km=10.0,
                time_utc="2026-08-25T00:00:00Z",
            )
        ]

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
    ) -> list[ThermalHotspotRecord]:
        return [
            ThermalHotspotRecord(
                lat=34.0,
                lon=-118.0,
                frp_mw=100.0,
            )
        ]

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        return MilitaryAwarenessSummary(
            status="ok",
            center_lat=lat,
            center_lon=lon,
            radius_km=radius_km,
            total_contacts=1,
            threat_level="low",
        )

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        return [
            SatellitePassRecord(
                sat_name="ISS",
                norad_id=25544,
                pass_start_utc="2026-08-25T12:00:00Z",
                pass_end_utc="2026-08-25T12:10:00Z",
                culmination_utc="2026-08-25T12:05:00Z",
                max_elevation_deg=45.0,
                pass_duration_seconds=600,
            )
        ]

    async def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[InfrastructureRecord]:
        return [
            InfrastructureRecord(
                infra_type="submarine_cable",
                name="MAREA Cable",
                country="USA",
            )
        ]

    async def render_sat_ortho(
        self,
        lat: float,
        lon: float,
        zoom: int = 21,
        size: int = 2048,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        return ImageryRenderResult(
            status="ok",
            tool_name="sat-ortho",
            output_path="/tmp/sat.png",
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
        return ImageryRenderResult(
            status="ok",
            tool_name="streetview-headings",
            output_path="/tmp/sv",
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
        return ImageryRenderResult(
            status="ok",
            tool_name="cesium-render",
            output_path="/tmp/globe.png",
        )

    async def get_weather(
        self,
        place: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherResult:
        return WeatherResult(status="ok", place=place or "Mock City", temperature_c=20.0, humidity_pct=50.0, wind_speed_kmh=10.0, conditions="Clear")

    async def get_weather_map(
        self,
        map_type: str = "radar",
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> WeatherMapResult:
        return WeatherMapResult(status="ok", map_type=map_type, frame_count=1)

    async def find_cctv_cameras(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 50,
    ) -> list[CctvCameraRecord]:
        return [CctvCameraRecord(camera_id="cam_mock", name="Mock Camera", lat=0.0, lon=0.0)]

    async def get_cctv_snapshot(self, camera_id: str) -> CctvSnapshotResult:
        return CctvSnapshotResult(camera_id=camera_id, status="ok", snapshot_url="https://example.com/cam.jpg")

    async def find_aircraft(
        self,
        callsign: str | None = None,
        icao24: str | None = None,
        registration: str | None = None,
        limit: int = 50,
    ) -> list[FlightRecord]:
        return [FlightRecord(icao24=icao24 or "mock_hex", callsign=callsign or "MOCK1", lat=0.0, lon=0.0)]

    async def get_aircraft_track(self, icao24: str, military: bool = False) -> AircraftTrackRecord:
        return AircraftTrackRecord(icao24=icao24, callsign="MOCK1", points=[])

    async def find_vessel(
        self,
        mmsi: str | None = None,
        imo: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[VesselRecord]:
        return [VesselRecord(mmsi=mmsi or "123456789", name=name or "Mock Ship", lat=0.0, lon=0.0)]

    async def get_vessel_track(self, mmsi: str) -> VesselTrackRecord:
        return VesselTrackRecord(mmsi=mmsi, name="Mock Ship", points=[])

    async def situation_brief(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> SituationBriefResult:
        return SituationBriefResult(status="ok", area_label=place or "Global")

    async def get_terrain_height(self, points: list[list[float]]) -> list[TerrainHeightRecord]:
        return [TerrainHeightRecord(lat=p[0], lon=p[1], elevation_m=10.0) for p in points]

    async def get_cyclones(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[CycloneRecord]:
        return [CycloneRecord(cyclone_id="CY01", name="Mock Cyclone", lat=0.0, lon=0.0)]

    async def get_active_fires(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        return [ThermalHotspotRecord(lat=0.0, lon=0.0, frp=10.0)]

    async def get_recent_imagery(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> dict:
        return {"status": "ok", "items": []}


@pytest.mark.unit
def test_gods_eye_view_service_protocol_conformance() -> None:
    service = MockGodsEyeViewService()
    assert isinstance(service, GodsEyeViewService)


@pytest.mark.asyncio
async def test_gods_eye_view_service_context_resolution() -> None:
    ctx = ServiceContext()
    service = MockGodsEyeViewService()

    ctx.provide(GODS_EYE_VIEW_SERVICE_KEY, service, provider="mock.provider")

    resolved = ctx.require(GODS_EYE_VIEW_SERVICE_KEY)
    assert resolved is not None
    assert isinstance(resolved, GodsEyeViewService)

    # Test calling service methods through DI container
    res = await resolved.query_analyst(layer="flights")
    assert res.status == "ok"
    assert res.total_matched == 1

    flights = await resolved.fetch_flights(military_only=True)
    assert len(flights) == 1
    assert flights[0].military is True

    quakes = await resolved.fetch_earthquakes()
    assert len(quakes) == 1
    assert quakes[0].magnitude == 5.0
