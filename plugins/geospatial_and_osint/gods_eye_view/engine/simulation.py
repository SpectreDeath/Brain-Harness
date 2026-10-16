"""Simulated MCP fallback payload generators for offline or disconnected environments."""

from __future__ import annotations

from typing import Any


def build_simulated_mcp_response(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    reason: str = "Subprocess offline fallback",
) -> dict[str, Any]:
    """Generate structured schema-compliant fallback response when MCP server is offline."""
    args = arguments or {}
    base_resp: dict[str, Any] = {
        "status": "simulated",
        "source": "simulated_fallback",
        "is_live": False,
        "tool": tool_name,
        "reason": reason,
    }

    if tool_name == "get_weather":
        loc = args.get("location", {})
        lat, lon = loc.get("lat", 40.7128), loc.get("lon", -74.0060)
        place = loc.get("place", f"{lat:.2f}, {lon:.2f}")
        base_resp.update({
            "summary": f"Weather at {place}: partly cloudy, 20°C, wind 14 km/h (simulated).",
            "location": {"label": place, "lat": lat, "lon": lon},
            "weather": {
                "conditions": "partly cloudy", "weather_code": 2, "temperature_c": 20.0,
                "feels_like_c": 20.5, "wind_kph": 14.0, "precipitation_mm": 0.0,
                "cloud_cover_pct": 35.0, "visibility_m": 10000,
            },
        })
    elif tool_name == "get_weather_map":
        m_type = args.get("map", "radar")
        base_resp.update({
            "summary": f"Latest {m_type} product composite (simulated).",
            "map": m_type, "title": f"Simulated {m_type.capitalize()} Composite",
            "coverage": "Continental Coverage", "time": "2026-10-10T12:00:00Z", "image": None,
        })
    elif tool_name == "find_cctv_cameras":
        area = args.get("area", {})
        place = area.get("place", "Area Center")
        lat, lon = area.get("lat", 40.7128), area.get("lon", -74.0060)
        base_resp.update({
            "summary": f"3 public cameras indexed near {place} (simulated).",
            "rows": [
                {"id": "cctv_sim_01", "name": "Downtown Central Intersection", "city": place, "provider": "Department of Transportation", "lat": lat, "lon": lon, "distance_km": 0.4},
                {"id": "cctv_sim_02", "name": "North Expressway Mile 12", "city": place, "provider": "Highway Authority", "lat": lat + 0.01, "lon": lon + 0.01, "distance_km": 1.2},
            ],
            "total": 2,
        })
    elif tool_name == "get_cctv_snapshot":
        cam_id = args.get("camera_id", "cam_01")
        base_resp.update({"summary": f"Current frame snapshot from {cam_id} (simulated).", "id": cam_id, "image": None})
    elif tool_name == "find_aircraft":
        q_id = args.get("callsign") or args.get("icao24") or args.get("registration") or "AF1"
        base_resp.update({
            "summary": f"Found aircraft matching {q_id} (simulated).",
            "rows": [{"id": "ae01cd", "callsign": str(q_id).upper(), "lat": 38.8951, "lon": -77.0364, "altitude_m": 9450, "speed_mps": 240.5, "course_deg": 180, "origin_country": "United States"}],
        })
    elif tool_name == "get_aircraft_track":
        target_hex = args.get("icao24", "ae01cd")
        base_resp.update({
            "summary": f"Recent 4 positions recorded for {target_hex} (simulated).",
            "icao24": target_hex, "total": 4,
            "points": [
                {"time": "2026-10-10T12:00:00Z", "lat": 38.80, "lon": -77.10, "altitude_m": 8500},
                {"time": "2026-10-10T12:05:00Z", "lat": 38.83, "lon": -77.08, "altitude_m": 8800},
                {"time": "2026-10-10T12:10:00Z", "lat": 38.86, "lon": -77.06, "altitude_m": 9100},
                {"time": "2026-10-10T12:15:00Z", "lat": 38.89, "lon": -77.03, "altitude_m": 9450},
            ],
        })
    elif tool_name == "find_vessel":
        q_vessel = args.get("mmsi") or args.get("name") or "PACIFIC"
        base_resp.update({
            "summary": f"Found vessel matching {q_vessel} (simulated).",
            "rows": [{"mmsi": "367123456", "name": str(q_vessel).upper(), "ship_type": "Cargo", "lat": 24.5, "lon": -81.8, "speed_kts": 14.2, "course_deg": 90}],
        })
    elif tool_name == "get_vessel_track":
        v_mmsi = args.get("mmsi", "367123456")
        base_resp.update({
            "summary": f"Recent track positions for vessel {v_mmsi} (simulated).",
            "mmsi": v_mmsi, "total": 3,
            "points": [
                {"time": "2026-10-10T11:00:00Z", "lat": 24.3, "lon": -82.2},
                {"time": "2026-10-10T11:30:00Z", "lat": 24.4, "lon": -82.0},
                {"time": "2026-10-10T12:00:00Z", "lat": 24.5, "lon": -81.8},
            ],
        })
    elif tool_name == "situation_brief":
        area = args.get("area", {})
        place = area.get("place", "Target Sector")
        base_resp.update({
            "summary": f"Situation brief for {place}: nominal maritime and aviation telemetry (simulated).",
            "area_label": place,
            "summary_lines": [
                "Weather: 20°C, partly cloudy, wind 14 km/h",
                "Aviation: 12 commercial and VIP flights in sector",
                "Maritime: 5 commercial vessels tracked in corridor",
                "Hazards: 0 active fires, 0 significant earthquakes in 24h",
            ],
            "sections": {
                "weather": {"status": "ok", "conditions": "partly cloudy"},
                "aviation": {"total_flights": 12},
                "maritime": {"total_vessels": 5},
                "hazards": {"fires": 0, "earthquakes": 0},
            },
        })
    elif tool_name == "get_terrain_height":
        pts = args.get("points", [])
        base_resp.update({
            "summary": f"Ground elevation computed for {len(pts)} points (simulated).",
            "rows": [{"lat": p.get("lat", 0.0), "lon": p.get("lon", 0.0), "elevation_m": 125.0} for p in pts],
        })
    elif tool_name == "get_cyclones":
        base_resp.update({
            "summary": "1 active tropical cyclone tracked in North Atlantic (simulated).",
            "storms": [{"id": "AL052026", "name": "SIMULATED CYCLONE", "classification": "Tropical Storm", "basin": "Atlantic", "lat": 18.5, "lon": -62.0, "wind_kt": 55, "pressure_hpa": 998}],
        })
    elif tool_name == "get_active_fires":
        base_resp.update({
            "summary": "Active fire perimeters from NASA FIRMS (simulated).",
            "rows": [{"id": "fire_sim_01", "name": "Simulated Forest Flare", "lat": 34.1, "lon": -118.2, "frp_mw": 45.0, "acres": 120}],
        })
    elif tool_name == "get_recent_imagery":
        base_resp.update({
            "summary": "Recent Sentinel-2 30m imagery available (simulated).",
            "satellite": "Sentinel-2", "product": "S30", "quality": "clear", "cloud_pct": 5.0, "acquisition_date": "2026-10-10",
        })
    else:
        base_resp["note"] = reason

    return base_resp
