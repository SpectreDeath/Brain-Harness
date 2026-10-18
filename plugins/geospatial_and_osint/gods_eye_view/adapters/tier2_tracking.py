"""Tier 2 Vessel, Aircraft, and Terrain Tracking MCP adapter methods."""

from __future__ import annotations

from typing import Any

from harness.services.gods_eye_view import (
    AircraftTrackRecord,
    FlightRecord,
    SituationBriefResult,
    TerrainHeightRecord,
    VesselRecord,
    VesselTrackRecord,
)
from ..tool_groups.analyst_tools import _build_area_dict


class Tier2TrackingMixin:
    """Mixin implementing tracking, aircraft, vessel, terrain, and brief tools."""

    _bridge: Any

    async def _query_mcp(self, tool_name: str, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        resp = await self._bridge.query_mcp_tool(tool_name, args)
        data = resp.get("result", {}).get("structuredContent", resp)
        return data, resp

    async def find_aircraft(
        self,
        callsign: str | None = None,
        icao24: str | None = None,
        registration: str | None = None,
        limit: int = 50,
    ) -> list[FlightRecord]:
        args: dict[str, Any] = {"limit": limit}
        if callsign:
            args["callsign"] = callsign
        elif icao24:
            args["icao24"] = icao24
        elif registration:
            args["registration"] = registration
        else:
            args["callsign"] = "AF1"
        data, _ = await self._query_mcp("find_aircraft", args)
        rows = data.get("rows", data.get("aircraft", []))
        return [
            FlightRecord(
                icao24=r.get("id") or r.get("icao24", "ae0001"),
                callsign=r.get("callsign"),
                origin_country=r.get("origin_country", "Unknown"),
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                altitude_m=r.get("altitude_m"),
                velocity_mps=r.get("speed_mps") or r.get("velocity_mps"),
                heading_deg=r.get("course_deg") or r.get("heading_deg"),
                vertical_rate_mps=r.get("vertical_rate_mps"),
                on_ground=r.get("on_ground", False),
                military=r.get("military", False),
                operator=r.get("operator"),
            )
            for r in rows
        ]

    async def get_aircraft_track(self, icao24: str, military: bool = False) -> AircraftTrackRecord:
        data, meta = await self._query_mcp("get_aircraft_track", {"icao24": icao24, "military": military})
        points = data.get("points", [])
        return AircraftTrackRecord(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            icao24=icao24,
            points=points,
            total_points=data.get("total", len(points)),
            summary=meta.get("summary", ""),
        )

    async def find_vessel(
        self,
        mmsi: str | None = None,
        imo: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[VesselRecord]:
        args: dict[str, Any] = {"limit": limit}
        if mmsi:
            args["mmsi"] = mmsi
        elif imo:
            args["imo"] = imo
        elif name:
            args["name"] = name
        else:
            args["name"] = "CARGO"
        data, _ = await self._query_mcp("find_vessel", args)
        rows = data.get("rows", data.get("vessels", []))
        return [
            VesselRecord(
                mmsi=r.get("mmsi", "367000000"),
                name=r.get("name", "VESSEL"),
                ship_type=r.get("ship_type", "Cargo"),
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                speed_kts=r.get("speed_kts", 0.0),
                heading_deg=r.get("course_deg") or r.get("heading_deg"),
                destination=r.get("destination"),
                length_m=r.get("length_m"),
                width_m=r.get("width_m"),
            )
            for r in rows
        ]

    async def get_vessel_track(self, mmsi: str) -> VesselTrackRecord:
        data, meta = await self._query_mcp("get_vessel_track", {"mmsi": mmsi})
        points = data.get("points", [])
        return VesselTrackRecord(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            mmsi=mmsi,
            points=points,
            total_points=data.get("total", len(points)),
            summary=meta.get("summary", ""),
        )

    async def situation_brief(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> SituationBriefResult:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Sector"}
        data, meta = await self._query_mcp("situation_brief", {"area": area})
        return SituationBriefResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            area_label=data.get("area_label", place or "Sector"),
            summary_lines=data.get("summary_lines", ["Area report generated"]),
            sections=data.get("sections", {}),
        )

    async def get_terrain_height(self, points: list[dict[str, float]]) -> list[TerrainHeightRecord]:
        data, _ = await self._query_mcp("get_terrain_height", {"points": points})
        rows = data.get("rows", data.get("elevations", []))
        return [
            TerrainHeightRecord(
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                elevation_m=r.get("elevation_m", 0.0),
            )
            for r in rows
        ]

    async def get_recent_imagery(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> dict[str, Any]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Gibraltar"}
        data, meta = await self._query_mcp("get_recent_imagery", {"area": area})
        return {
            "status": meta.get("status", "ok"),
            "source": meta.get("source", "mcp_live"),
            "is_live": meta.get("is_live", True),
            "summary": meta.get("summary", ""),
            "satellite": data.get("satellite"),
            "product": data.get("product"),
            "quality": data.get("quality"),
            "cloud_pct": data.get("cloud_pct"),
            "acquisition_date": data.get("acquisition_date"),
        }
