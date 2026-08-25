"""Kernel Service Registration & DI Integration tests for GodsEyeViewService."""

from __future__ import annotations

import pytest
from harness.kernel.context import ServiceContext
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
