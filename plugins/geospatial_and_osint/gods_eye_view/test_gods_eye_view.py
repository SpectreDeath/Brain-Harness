"""Comprehensive test suite for God's Eye View plugin, spatial index, and query pipeline."""

from __future__ import annotations

import asyncio
import pytest
from harness.kernel.context import ServiceContext
from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY, GodsEyeViewService

from plugins.geospatial_and_osint.gods_eye_view.async_runner import run_sync_safe
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
from plugins.geospatial_and_osint.gods_eye_view.models import FlightRecord, InfrastructureRecord
from plugins.geospatial_and_osint.gods_eye_view.query_pipeline import QuerySessionStore, SpatialQueryPipeline
from plugins.geospatial_and_osint.gods_eye_view.spatial_index import SpatialHashGrid, point_in_polygon
from plugins.geospatial_and_osint.gods_eye_view.telemetry_cache import TelemetryCache


@pytest.mark.unit
def test_haversine_and_point_in_polygon() -> None:
    # NY to London ~ 5570 km
    dist = haversine_km(40.7128, -74.0060, 51.5074, -0.1278)
    assert 5500 < dist < 5700
    assert haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0

    # Polygon point-in-ring test (triangle around Texas)
    triangle_texas = [(36.5, -103.0), (36.5, -94.0), (25.8, -97.5)]
    # Austin, TX (30.2672, -97.7431) inside triangle
    assert point_in_polygon(30.2672, -97.7431, triangle_texas) is True
    # Seattle, WA (47.6062, -122.3321) outside triangle
    assert point_in_polygon(47.6062, -122.3321, triangle_texas) is False


@pytest.mark.unit
def test_spatial_hash_grid_operations() -> None:
    grid = SpatialHashGrid[dict](cell_size_deg=1.0, lat_extractor=lambda d: d["lat"], lon_extractor=lambda d: d["lon"])

    items = [
        {"id": "austin", "lat": 30.2672, "lon": -97.7431},
        {"id": "san_antonio", "lat": 29.4241, "lon": -98.4936},
        {"id": "dallas", "lat": 32.7767, "lon": -96.7970},
        {"id": "london", "lat": 51.5074, "lon": -0.1278},
    ]
    grid.bulk_insert(items, key_fn=lambda x: x["id"])
    assert len(grid) == 4

    # 1. Radius query: within 150km of Austin should find Austin and San Antonio (~120km), but not Dallas (~300km) or London
    near_austin = grid.query_radius(30.2672, -97.7431, radius_km=150.0)
    assert len(near_austin) == 2
    matched_ids = [item["id"] for _, item in near_austin]
    assert "austin" in matched_ids
    assert "san_antonio" in matched_ids
    assert "dallas" not in matched_ids

    # 2. Bounding box query over Texas
    texas_bbox = grid.query_bbox(north=37.0, south=25.0, west=-107.0, east=-93.0)
    assert len(texas_bbox) == 3
    assert all(item["id"] != "london" for item in texas_bbox)

    # 3. k-NN concentric expansion query
    knn_results = grid.query_knn(lat=30.0, lon=-97.0, k=2)
    assert len(knn_results) == 2
    assert knn_results[0][0] <= knn_results[1][0]

    # 4. Remove and update
    assert grid.remove("london") is True
    assert len(grid) == 3
    assert grid.remove("non_existent") is False


@pytest.mark.asyncio
async def test_telemetry_cache_single_flight_and_ttl() -> None:
    cache = TelemetryCache[list[str]](stale_ratio=0.5)
    fetch_count = 0

    async def mock_fetch() -> list[str]:
        nonlocal fetch_count
        fetch_count += 1
        await asyncio.sleep(0.01)
        return [f"record_{fetch_count}"]

    # 1. Concurrent requests should trigger only 1 fetch via single-flight lock
    tasks = [cache.get_or_fetch("test_key", mock_fetch, ttl_seconds=1.0) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert fetch_count == 1
    assert all(r == ["record_1"] for r in results)

    # 2. Subsequent call should hit cache immediately
    cached_res = await cache.get_or_fetch("test_key", mock_fetch, ttl_seconds=1.0)
    assert cached_res == ["record_1"]
    assert fetch_count == 1

    # 3. Force refresh overrides cache
    refreshed_res = await cache.get_or_fetch("test_key", mock_fetch, ttl_seconds=1.0, force_refresh=True)
    assert refreshed_res == ["record_2"]
    assert fetch_count == 2

    # Stats inspection
    stats = cache.get_stats()
    assert stats["hits"] >= 1
    assert stats["cached_keys_count"] == 1


@pytest.mark.unit
def test_spatial_query_pipeline_predicates_and_aggregations() -> None:
    records = [
        {"id": "1", "altitude_m": 12000, "operator": "Air Force One", "military": True, "lat": 38.89, "lon": -77.03},
        {"id": "2", "altitude_m": 8500, "operator": "Delta Air Lines", "military": False, "lat": 33.64, "lon": -84.42},
        {"id": "3", "altitude_m": 3000, "operator": "Cessna Skyhawk", "military": False, "lat": 30.26, "lon": -97.74},
    ]

    # Test filtering with compound predicates
    filtered = SpatialQueryPipeline.filter_records(
        records=records,
        filters=[
            {"field": "altitude_m", "op": "gte", "value": 8000},
            {"field": "operator", "op": "contains", "value": "air"},
        ],
    )
    assert len(filtered) == 2
    assert {r["id"] for r in filtered} == {"1", "2"}

    # Test aggregations
    aggs = SpatialQueryPipeline.compute_aggregations(records)
    assert aggs["count"] == 3
    assert aggs["avg_altitude_m"] == round((12000 + 8500 + 3000) / 3, 2)
    assert aggs["max_altitude_m"] == 12000
    assert aggs["min_altitude_m"] == 3000

    # Test RFC 7946 GeoJSON export
    geojson = SpatialQueryPipeline.to_geojson(records, layer_name="test_flights")
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 3
    f0 = geojson["features"][0]
    assert f0["geometry"]["type"] == "Point"
    assert f0["geometry"]["coordinates"] == [-77.03, 38.89]
    assert f0["properties"]["operator"] == "Air Force One"


@pytest.mark.unit
def test_query_session_store() -> None:
    store = QuerySessionStore(max_sessions=3, session_ttl_sec=10.0)
    tok1 = store.save_session([{"a": 1}])
    tok2 = store.save_session([{"b": 2}])

    assert store.get_session(tok1) == [{"a": 1}]
    assert store.get_session("invalid_tok") is None


@pytest.mark.unit
def test_async_runner_safe_execution() -> None:
    async def sample_coro(val: int) -> int:
        await asyncio.sleep(0.01)
        return val * 2

    # 1. Run from synchronous context
    res1 = run_sync_safe(sample_coro(21))
    assert res1 == 42


@pytest.mark.asyncio
async def test_async_runner_inside_active_event_loop() -> None:
    # 2. Run from inside an active async event loop (tests re-entrance safety)
    async def inner_coro() -> str:
        await asyncio.sleep(0.01)
        return "loop_safe"

    res = run_sync_safe(inner_coro())
    assert res == "loop_safe"


@pytest.mark.asyncio
async def test_engine_fetch_flights_and_caching() -> None:
    engine = GodsEyeViewEngine()
    flights1 = await engine.fetch_flights(limit=10)
    assert len(flights1) > 0

    # Second fetch should hit cache
    flights2 = await engine.fetch_flights(limit=10)
    assert len(flights2) == len(flights1)

    # Test military filter
    mil_flights = await engine.fetch_flights(military_only=True)
    for mf in mil_flights:
        assert mf.military is True


@pytest.mark.asyncio
async def test_engine_fetch_vessels_and_earthquakes() -> None:
    engine = GodsEyeViewEngine()
    vessels = await engine.fetch_vessels(ship_type="Container")
    assert len(vessels) >= 1

    quakes = await engine.fetch_earthquakes(min_magnitude=4.0)
    assert len(quakes) > 0
    for q in quakes:
        assert q.magnitude >= 4.0


@pytest.mark.asyncio
async def test_engine_military_awareness_and_satellite_passes() -> None:
    engine = GodsEyeViewEngine()
    summary = await engine.query_military_awareness(lat=49.4369, lon=7.6003, radius_km=250.0)
    assert summary.status == "ok"
    assert len(summary.nearest_installations) > 0

    passes = await engine.calculate_satellite_passes(lat=38.8951, lon=-77.0364)
    assert len(passes) >= 1
    assert passes[0].norad_id == 25544


@pytest.mark.unit
def test_infrastructure_store_query_with_spatial_grid() -> None:
    store = InfrastructureStore()
    cables = store.query(infra_type="submarine_cable", search_query="MAREA")
    assert len(cables) >= 1

    # Spatial query near Virginia Beach
    landing_pts = store.query(infra_type="landing_point", lat=36.85, lon=-75.97, radius_km=50.0)
    assert len(landing_pts) >= 1


@pytest.mark.asyncio
async def test_analyst_query_pipeline_and_geojson() -> None:
    engine = GodsEyeViewEngine()
    res = await engine.query_analyst(
        layer="flights",
        filters=[{"field": "altitude_m", "op": "gt", "value": 5000}],
        include_geojson=True,
    )
    assert res.status == "ok"
    assert res.total_matched > 0
    assert res.geojson is not None
    assert res.geojson["type"] == "FeatureCollection"
    assert "avg_altitude_m" in res.aggregations

    # Follow-up session query
    res2 = await engine.query_analyst(
        layer="flights",
        filters=[{"field": "military", "op": "eq", "value": "True"}],
        follow_up_token=res.follow_up_token,
    )
    assert res2.status == "ok"
    assert res2.total_matched <= res.total_matched


@pytest.mark.unit
def test_standalone_tools_with_async_runner() -> None:
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

    an = gev_analyst_query(layer="earthquakes", filters=[{"field": "magnitude", "op": "gte", "value": 4.0}])
    assert isinstance(an, dict)
    assert "geojson" in an


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

    res = await resolved_service.query_analyst(layer="flights")
    assert res.status == "ok"

    await plugin.on_disable()
    await plugin.on_unload()
