"""Standalone CLI tool entrypoints for the God's Eye View geospatial intelligence plugin.

Decomposed into domain-partitioned tool_groups (AGENTS.md Rule 18 & monolith decomposition standards).
All 24 tools re-exported here for 100% backward compatibility.
"""

from __future__ import annotations

from .tool_groups import (
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

__all__ = [
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
