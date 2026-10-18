"""Characterization test suite for God's Eye View tools and output schemas.

Preserves behavioral and payload shape invariants (Rule 13) before decomposition.
"""

from __future__ import annotations

import pytest

from plugins.geospatial_and_osint.gods_eye_view.tools import (
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


@pytest.mark.unit
def test_flight_and_aircraft_tools_characterization() -> None:
    """Verify live flight fetch and aircraft lookup return expected payload types."""
    flights = gev_fetch_live_flights(military_only=True)
    assert isinstance(flights, list)
    assert len(flights) > 0
    first = flights[0]
    assert "icao24" in first
    assert "lat" in first
    assert "lon" in first
    assert first.get("military") is True

    ac = gev_find_aircraft(icao24="ae01d5")
    assert isinstance(ac, dict)
    assert "status" in ac


@pytest.mark.unit
def test_vessel_tools_characterization() -> None:
    """Verify AIS vessel fetch and vessel lookup characterization."""
    vessels = gev_fetch_ais_vessels(destination="NORFOLK")
    assert isinstance(vessels, list)
    assert len(vessels) > 0
    first = vessels[0]
    assert "mmsi" in first
    assert "name" in first
    assert "lat" in first

    v = gev_find_vessel(name="EVER")
    assert isinstance(v, dict)
    assert "status" in v


@pytest.mark.unit
def test_environmental_tools_characterization() -> None:
    """Verify seismic, thermal, and cyclone tools characterization."""
    quakes = gev_fetch_earthquakes(min_magnitude=3.0)
    assert isinstance(quakes, list)
    assert len(quakes) > 0
    q = quakes[0]
    assert "event_id" in q
    assert "magnitude" in q

    hotspots = gev_fetch_firms_hotspots(min_frp=50.0)
    assert isinstance(hotspots, list)
    assert len(hotspots) > 0
    h = hotspots[0]
    assert "brightness_kelvin" in h
    assert "frp_mw" in h

    cyclones = gev_get_cyclones()
    assert isinstance(cyclones, dict)
    assert "status" in cyclones


@pytest.mark.unit
def test_tactical_and_infrastructure_tools_characterization() -> None:
    """Verify military awareness and infrastructure query return expected payload shapes."""
    summary = gev_query_military_awareness(lat=38.8951, lon=-77.0364, radius_km=300.0)
    assert isinstance(summary, dict)
    assert summary.get("status") == "ok"
    assert "threat_level" in summary
    assert "air_contacts" in summary
    assert "maritime_contacts" in summary

    infras = gev_query_infrastructure(infra_type="submarine_cable", query="MAREA")
    assert isinstance(infras, list)
    assert len(infras) > 0
    first_infra = infras[0]
    assert first_infra.get("name") == "MAREA Transatlantic Cable"
    assert "lat" in first_infra


@pytest.mark.unit
def test_analyst_query_characterization() -> None:
    """Verify multi-layer analyst query returns status, layer, items, and aggregations."""
    res = gev_analyst_query(layer="flights")
    assert isinstance(res, dict)
    assert res.get("status") == "ok"
    assert res.get("layer") == "flights"
    assert "items" in res
    assert "total_matched" in res
