"""Tier 2 Environmental & Surveillance MCP sensing adapter methods."""

from __future__ import annotations

from typing import Any

from harness.services.gods_eye_view import (
    CctvCameraRecord,
    CctvSnapshotResult,
    CycloneRecord,
    ThermalHotspotRecord,
    WeatherMapResult,
    WeatherResult,
)
from ..tool_groups.analyst_tools import _build_area_dict


class Tier2SensingMixin:
    """Mixin implementing sensing, camera, and weather tools."""

    _bridge: Any

    async def _query_mcp(self, tool_name: str, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        resp = await self._bridge.query_mcp_tool(tool_name, args)
        data = resp.get("result", {}).get("structuredContent", resp)
        return data, resp

    async def get_weather(self, place: str | None = None, lat: float | None = None, lon: float | None = None) -> WeatherResult:
        args: dict[str, Any] = {}
        if place:
            args["location"] = place
        elif lat is not None and lon is not None:
            args["lat"] = lat
            args["lon"] = lon
        else:
            args["location"] = "Washington, DC"
        data, meta = await self._query_mcp("get_weather", args)
        return WeatherResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            location=data.get("location", {}),
            weather=data.get("weather", {}),
            summary=meta.get("summary", ""),
        )

    async def get_weather_map(
        self,
        map_type: str = "radar",
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> WeatherMapResult:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "United States"}
        data, meta = await self._query_mcp("get_weather_map", {"map_type": map_type, "area": area})
        return WeatherMapResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            map_type=map_type,
            title=data.get("title", f"Weather {map_type.capitalize()} Map"),
            coverage=data.get("coverage", "Regional"),
            image_url_or_b64=data.get("image_url") or data.get("b64"),
        )

    async def find_cctv_cameras(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 50,
    ) -> list[CctvCameraRecord]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "Downtown"}
        data, _ = await self._query_mcp("find_cctv_cameras", {"area": area, "limit": limit})
        rows = data.get("rows", data.get("cameras", data.get("items", [])))
        return [
            CctvCameraRecord(
                id=c.get("id", "cctv_01"),
                camera_id=c.get("camera_id") or c.get("id", "cctv_01"),
                name=c.get("name", "Public Camera"),
                lat=c.get("lat", 0.0),
                lon=c.get("lon", 0.0),
                city=c.get("city", place or "Metro"),
                provider=c.get("provider", "DOT"),
                heading_deg=c.get("heading_deg"),
            )
            for c in rows
        ]

    async def get_cctv_snapshot(self, camera_id: str) -> CctvSnapshotResult:
        data, meta = await self._query_mcp("get_cctv_snapshot", {"camera_id": camera_id})
        return CctvSnapshotResult(
            status=meta.get("status", "ok"),
            source=meta.get("source", "mcp_live"),
            is_live=meta.get("is_live", True),
            camera_id=camera_id,
            summary=meta.get("summary", ""),
            image_url_or_b64=data.get("image_url") or data.get("b64"),
        )

    async def get_cyclones(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[CycloneRecord]:
        args: dict[str, Any] = {}
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km)
        if area:
            args["area"] = area
        data, _ = await self._query_mcp("get_cyclones", args)
        storms = data.get("storms", data.get("rows", []))
        return [
            CycloneRecord(
                id=s.get("id", "AL00"),
                name=s.get("name", "TROPICAL CYCLONE"),
                classification=s.get("classification", "Tropical Storm"),
                basin=s.get("basin", "Atlantic"),
                lat=s.get("lat", 0.0),
                lon=s.get("lon", 0.0),
                wind_kt=s.get("wind_kt"),
                pressure_hpa=s.get("pressure_hpa"),
            )
            for s in storms
        ]

    async def get_active_fires(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        area = _build_area_dict(place=place, bbox=bbox, lat=lat, lon=lon, radius_km=radius_km) or {"place": "California"}
        data, _ = await self._query_mcp("get_active_fires", {"area": area, "limit": limit})
        rows = data.get("rows", data.get("fires", []))
        return [
            ThermalHotspotRecord(
                lat=r.get("lat", 0.0),
                lon=r.get("lon", 0.0),
                frp_mw=r.get("frp_mw", 0.0),
                confidence=r.get("confidence", "nominal"),
                brightness_kelvin=r.get("brightness_k", r.get("brightness_kelvin", 300.0)),
                acquisition_date=r.get("acq_date") or "",
                satellite="SIMULATED" if "sim" in r.get("id", "") else "NOAA-20",
                daynight="D",
            )
            for r in rows
        ]
