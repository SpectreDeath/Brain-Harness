"""Modular geospatial intelligence and OSINT analytics engine package."""

from __future__ import annotations

from ..infrastructure_store import haversine_km
from .analyst import execute_analyst_query
from .aviation_maritime import (
    fetch_flights,
    fetch_vessels,
    raw_fetch_opensky,
)
from .core import GodsEyeViewEngine
from .environmental import (
    fetch_earthquakes,
    fetch_firms_hotspots,
    raw_fetch_usgs,
)
from .mock_data import (
    EARTH_R_KM,
    MOCK_EARTHQUAKES,
    MOCK_FIRMS,
    MOCK_FLIGHTS,
    MOCK_VESSELS,
    asyncio_wrap,
)
from .resolvers import resolve_gods_eye_view_engine
from .simulation import build_simulated_mcp_response
from .tactical import (
    calculate_satellite_passes,
    query_military_awareness,
)

__all__ = [
    "EARTH_R_KM",
    "GodsEyeViewEngine",
    "MOCK_EARTHQUAKES",
    "MOCK_FIRMS",
    "MOCK_FLIGHTS",
    "MOCK_VESSELS",
    "asyncio_wrap",
    "build_simulated_mcp_response",
    "calculate_satellite_passes",
    "execute_analyst_query",
    "fetch_earthquakes",
    "fetch_firms_hotspots",
    "fetch_flights",
    "fetch_vessels",
    "haversine_km",
    "query_military_awareness",
    "raw_fetch_opensky",
    "raw_fetch_usgs",
    "resolve_gods_eye_view_engine",
]
