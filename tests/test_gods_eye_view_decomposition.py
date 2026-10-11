"""Contract test suite for GodsEyeViewEngine architecture deepening and decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest
from unittest.mock import MagicMock

from harness.kernel.context import ServiceContext
from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY, GodsEyeViewService
from plugins.geospatial_and_osint.gods_eye_view.engine import (
    EARTH_R_KM,
    GodsEyeViewEngine,
    MOCK_EARTHQUAKES,
    MOCK_FIRMS,
    MOCK_FLIGHTS,
    MOCK_VESSELS,
    asyncio_wrap,
    haversine_km,
    resolve_gods_eye_view_engine,
)
from plugins.geospatial_and_osint.gods_eye_view.main import GodsEyeViewPlugin, plugin


@pytest.mark.unit
def test_facade_reexports_and_backward_compatibility() -> None:
    """Verify all public symbols are accessible from package root facade."""
    assert issubclass(GodsEyeViewEngine, object)
    assert callable(haversine_km)
    assert EARTH_R_KM == 6371.0
    assert len(MOCK_FLIGHTS) >= 5
    assert len(MOCK_VESSELS) >= 4
    assert len(MOCK_EARTHQUAKES) >= 3
    assert len(MOCK_FIRMS) >= 3
    assert callable(asyncio_wrap)
    assert callable(resolve_gods_eye_view_engine)


@pytest.mark.unit
def test_submodule_line_counts_strictly_bounded() -> None:
    """Verify all submodules in engine/ remain strictly under 200 lines per Rule 11."""
    pkg_dir = Path("plugins/geospatial_and_osint/gods_eye_view/engine")
    py_files = list(pkg_dir.glob("*.py"))
    assert len(py_files) >= 7, f"Expected at least 7 submodules, found {len(py_files)}"

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines < 200, f"Module {py_file.name} has {lines} lines, exceeding 200 limit"


@pytest.mark.unit
def test_engine_initialization_and_stores() -> None:
    """Verify GodsEyeViewEngine correctly initializes internal stores and timeout."""
    engine = GodsEyeViewEngine()
    assert engine.infra_store is not None
    assert engine.cache is not None
    assert engine.session_store is not None
    assert engine.http_timeout == 8.0


@pytest.mark.asyncio
async def test_aviation_maritime_fetchers_filtering() -> None:
    """Verify flight and vessel filtering logic in decomposed engine."""
    engine = GodsEyeViewEngine()

    military_flights = await engine.fetch_flights(military_only=True)
    assert len(military_flights) > 0
    assert all(f.military for f in military_flights)

    us_vessels = await engine.fetch_vessels(destination="NORFOLK")
    assert len(us_vessels) > 0
    assert all("NORFOLK" in (v.destination or "") for v in us_vessels)


@pytest.mark.asyncio
async def test_environmental_fetchers_filtering() -> None:
    """Verify seismic and thermal hotspot filtering thresholds."""
    engine = GodsEyeViewEngine()

    major_quakes = await engine.fetch_earthquakes(min_magnitude=3.0)
    assert len(major_quakes) > 0
    assert all(q.magnitude >= 3.0 for q in major_quakes)

    intense_fires = await engine.fetch_firms_hotspots(min_frp=100.0)
    assert len(intense_fires) > 0
    assert all(h.frp_mw >= 100.0 for h in intense_fires)


@pytest.mark.asyncio
async def test_tactical_military_awareness_summary() -> None:
    """Verify tactical contact aggregation and threat level classification."""
    engine = GodsEyeViewEngine()
    summary = await engine.query_military_awareness(
        lat=38.8951, lon=-77.0364, radius_km=500.0, include_bases=True
    )
    assert summary.status == "ok"
    assert summary.radius_km == 500.0
    assert summary.total_contacts == len(summary.air_contacts) + len(summary.maritime_contacts)
    assert summary.threat_level in ["low", "moderate", "elevated", "high"]


@pytest.mark.asyncio
async def test_satellite_pass_predictions() -> None:
    """Verify satellite orbital passes calculation over ground coordinates."""
    engine = GodsEyeViewEngine()
    passes = await engine.calculate_satellite_passes(
        lat=40.7128, lon=-74.0060, sat_name="ISS", horizon_hours=24
    )
    assert len(passes) >= 2
    for p in passes:
        assert "ISS" in p.sat_name
        assert p.pass_duration_seconds > 0
        assert p.max_elevation_deg >= 0.0


@pytest.mark.asyncio
async def test_analyst_query_pipeline_and_session_chaining() -> None:
    """Verify multi-layer analyst queries, GeoJSON generation, and session follow-up."""
    engine = GodsEyeViewEngine()
    res = await engine.query_analyst(layer="flights", include_geojson=True)
    assert res.status == "ok"
    assert res.total_matched > 0
    assert res.geojson is not None
    assert res.geojson["type"] == "FeatureCollection"
    assert res.follow_up_token is not None

    follow_up = await engine.query_analyst(layer="flights", follow_up_token=res.follow_up_token)
    assert follow_up.status == "ok"
    assert follow_up.total_matched == res.total_matched


@pytest.mark.unit
def test_single_seam_resolver() -> None:
    """Verify resolve_gods_eye_view_engine with and without ServiceContext per Rule 58."""
    engine_fallback = resolve_gods_eye_view_engine()
    assert isinstance(engine_fallback, GodsEyeViewEngine)

    ctx = MagicMock(spec=ServiceContext)
    mock_service = MagicMock(spec=GodsEyeViewService)
    custom_engine = GodsEyeViewEngine()
    mock_service._engine = custom_engine
    ctx.optional.return_value = mock_service

    resolved = resolve_gods_eye_view_engine(ctx)
    assert resolved is custom_engine
    ctx.optional.assert_called_once_with(GODS_EYE_VIEW_SERVICE_KEY)


@pytest.mark.unit
def test_plugin_singleton_and_ioc_registration() -> None:
    """Verify module-level singleton export per Rule 45."""
    assert isinstance(plugin, GodsEyeViewPlugin)
    assert GODS_EYE_VIEW_SERVICE_KEY in plugin.provides
