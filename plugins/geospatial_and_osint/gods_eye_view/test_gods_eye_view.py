"""Comprehensive test suite for God's Eye View plugin and spatial analytics engine."""

from __future__ import annotations

import pytest
from harness.kernel.context import ServiceContext
from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY, GodsEyeViewService

from plugins.geospatial_and_osint.gods_eye_view.cli_bridge import NodeCliBridge
from plugins.geospatial_and_osint.gods_eye_view.engine import GodsEyeViewEngine, haversine_km
from plugins.geospatial_and_osint.gods_eye_view.infrastructure_store import InfrastructureStore
from plugins.geospatial_and_osint.gods_eye_view.main import (
    GodsEyeViewPlugin,
    gev_analyst_query,
    gev_calculate_satellite_passes,
    gev_capture_streetview_headings,
    gev_fetch_ais_vessels,
    gev_fetch_earthquakes,
    gev_fetch_firms_hotspots,
    gev_fetch_live_flights,
    gev_query_infrastructure,
    gev_query_military_awareness,
    gev_render_globe_snapshot,
    gev_render_sat_ortho,
)


@pytest.mark.unit
def test_haversine_distance_calculation() -> None:
    # Distance between New York (40.7128, -74.0060) and London (51.5074, -0.1278) ~ 5570 km
    dist = haversine_km(40.7128, -74.0060, 51.5074, -0.1278)
    assert 5500 < dist < 5700

    # Distance to same point should be 0.0
    assert haversine_km(38.8951, -77.0364, 38.8951, -77.0364) == 0.0


@pytest.mark.asyncio
async def test_engine_fetch_flights_filtering() -> None:
    engine = GodsEyeViewEngine()
    flights = await engine.fetch_flights(limit=10)
    assert len(flights) > 0
    assert any(f.icao24 for f in flights)

    # Test military filter
    mil_flights = await engine.fetch_flights(military_only=True)
    for mf in mil_flights:
        assert mf.military is True


@pytest.mark.asyncio
async def test_engine_fetch_vessels() -> None:
    engine = GodsEyeViewEngine()
    vessels = await engine.fetch_vessels(ship_type="Container")
    assert len(vessels) >= 1
    assert any("container" in v.ship_type.lower() or "cargo" in v.ship_type.lower() for v in vessels)


@pytest.mark.asyncio
async def test_engine_fetch_earthquakes() -> None:
    engine = GodsEyeViewEngine()
    quakes = await engine.fetch_earthquakes(min_magnitude=4.0)
    assert len(quakes) > 0
    for q in quakes:
        assert q.magnitude >= 4.0
        assert q.depth_km >= 0.0


@pytest.mark.asyncio
async def test_engine_fetch_firms_hotspots() -> None:
    engine = GodsEyeViewEngine()
    hotspots = await engine.fetch_firms_hotspots(min_frp=50.0)
    assert len(hotspots) > 0
    for h in hotspots:
        assert h.frp_mw >= 50.0


@pytest.mark.asyncio
async def test_engine_military_awareness_corridor() -> None:
    engine = GodsEyeViewEngine()
    # Query near Ramstein Air Base coordinates (49.4369, 7.6003)
    summary = await engine.query_military_awareness(
        lat=49.4369,
        lon=7.6003,
        radius_km=250.0,
        include_bases=True,
    )
    assert summary.status == "ok"
    assert summary.center_lat == 49.4369
    assert summary.radius_km == 250.0
    assert len(summary.nearest_installations) > 0
    assert any("ramstein" in inst["name"].lower() for inst in summary.nearest_installations)


@pytest.mark.asyncio
async def test_engine_satellite_pass_prediction() -> None:
    engine = GodsEyeViewEngine()
    passes = await engine.calculate_satellite_passes(
        lat=38.8951,
        lon=-77.0364,
        sat_name="ISS",
        norad_id=25544,
        horizon_hours=24,
    )
    assert len(passes) >= 1
    p = passes[0]
    assert p.norad_id == 25544
    assert p.max_elevation_deg > 0.0
    assert p.pass_duration_seconds > 0


@pytest.mark.unit
def test_infrastructure_store_query() -> None:
    store = InfrastructureStore()
    # Test submarine cables
    cables = store.query(infra_type="submarine_cable", search_query="MAREA")
    assert len(cables) >= 1
    assert "marea" in cables[0].name.lower()

    # Test spatial proximity query (near Virginia Beach)
    landing_pts = store.query(infra_type="landing_point", lat=36.85, lon=-75.97, radius_km=50.0)
    assert len(landing_pts) >= 1

    # Test datacenters
    dcs = store.query(infra_type="datacenter", search_query="Ashburn")
    assert len(dcs) >= 1


@pytest.mark.asyncio
async def test_analyst_query_engine_and_followup_memory() -> None:
    engine = GodsEyeViewEngine()
    # 1. Initial query: flights with altitude > 5000
    res1 = await engine.query_analyst(
        layer="flights",
        filters=[{"field": "altitude_m", "op": "gt", "value": 5000}],
    )
    assert res1.status == "ok"
    assert res1.total_matched > 0
    assert res1.follow_up_token is not None
    assert "count" in res1.aggregations

    # 2. Follow-up query using session token: filter down to military only
    res2 = await engine.query_analyst(
        layer="flights",
        filters=[{"field": "military", "op": "eq", "value": "True"}],
        follow_up_token=res1.follow_up_token,
    )
    assert res2.status == "ok"
    assert res2.total_matched <= res1.total_matched


@pytest.mark.asyncio
async def test_node_cli_bridge_diagnostics() -> None:
    bridge = NodeCliBridge()
    # Satellite ortho
    ortho_res = await bridge.render_sat_ortho(lat=30.266, lon=-97.737, zoom=21)
    assert ortho_res.status in ("ok", "simulated", "error")
    assert ortho_res.tool_name == "sat-ortho"

    # Streetview headings
    sv_res = await bridge.capture_streetview_headings(lat=30.266, lon=-97.737)
    assert sv_res.status in ("ok", "simulated", "error")
    assert sv_res.tool_name == "streetview-headings"

    # 3D Globe snapshot
    globe_res = await bridge.render_globe_snapshot(lat=30.266, lon=-97.737, style="surveillance")
    assert globe_res.status in ("ok", "simulated", "error")
    assert globe_res.tool_name == "cesium-render"


@pytest.mark.unit
def test_standalone_tool_functions() -> None:
    # Test synchronous standalone wrappers exported for tool registry
    fl = gev_fetch_live_flights(limit=5)
    assert isinstance(fl, list)

    vs = gev_fetch_ais_vessels(limit=5)
    assert isinstance(vs, list)

    eq = gev_fetch_earthquakes(min_magnitude=3.0)
    assert isinstance(eq, list)

    fm = gev_fetch_firms_hotspots(min_frp=10.0)
    assert isinstance(fm, list)

    mil = gev_query_military_awareness(lat=49.4369, lon=7.6003, radius_km=100.0)
    assert isinstance(mil, dict)
    assert mil.get("status") == "ok"

    sat = gev_calculate_satellite_passes(lat=38.89, lon=-77.03)
    assert isinstance(sat, list)

    inf = gev_query_infrastructure(infra_type="dam", query="Hoover")
    assert isinstance(inf, list)
    assert len(inf) >= 1

    an = gev_analyst_query(layer="earthquakes", filters=[{"field": "magnitude", "op": "gte", "value": 4.0}])
    assert isinstance(an, dict)
    assert an.get("status") == "ok"

    ortho = gev_render_sat_ortho(lat=37.7749, lon=-122.4194)
    assert isinstance(ortho, dict)

    sv = gev_capture_streetview_headings(lat=37.7749, lon=-122.4194)
    assert isinstance(sv, dict)

    gl = gev_render_globe_snapshot(lat=37.7749, lon=-122.4194, style="noir")
    assert isinstance(gl, dict)


@pytest.mark.asyncio
async def test_plugin_lifecycle_and_di() -> None:
    plugin = GodsEyeViewPlugin()
    ctx = ServiceContext()

    assert GODS_EYE_VIEW_SERVICE_KEY in plugin.provides

    await plugin.on_load(ctx)
    await plugin.on_enable()

    resolved_service = ctx.require(GODS_EYE_VIEW_SERVICE_KEY)
    assert resolved_service is not None
    assert isinstance(resolved_service, GodsEyeViewService)

    # Test service methods via resolved DI protocol
    res = await resolved_service.query_analyst(layer="flights")
    assert res.status == "ok"

    await plugin.on_disable()
    await plugin.on_unload()
