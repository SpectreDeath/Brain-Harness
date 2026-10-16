"""Pydantic v2 data models for God's Eye View plugin entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from harness.services.gods_eye_view import (
    AircraftTrackRecord,
    CctvCameraRecord,
    CctvSnapshotResult,
    CycloneRecord,
    EarthquakeRecord,
    FlightRecord,
    ImageryRenderResult,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    MilitaryContact,
    SatellitePassRecord,
    SituationBriefResult,
    TerrainHeightRecord,
    ThermalHotspotRecord,
    VesselRecord,
    VesselTrackRecord,
    WeatherMapResult,
    WeatherResult,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalystQueryResult(BaseModel):
    """Result of multi-layer spatial query engine execution."""

    status: str = Field(default="ok", description="Status indicator")
    layer: str = Field(..., description="Target query layer")
    total_matched: int = Field(default=0, description="Total matching records")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Matching entity records")
    aggregations: dict[str, Any] = Field(default_factory=dict, description="Computed summary statistics")
    geojson: dict[str, Any] | None = Field(default=None, description="Standard RFC 7946 GeoJSON FeatureCollection representation")
    follow_up_token: str | None = Field(default=None, description="Token to reference in follow-up queries")


__all__ = [
    "AircraftTrackRecord",
    "AnalystQueryResult",
    "CctvCameraRecord",
    "CctvSnapshotResult",
    "CycloneRecord",
    "EarthquakeRecord",
    "FlightRecord",
    "ImageryRenderResult",
    "InfrastructureRecord",
    "MilitaryAwarenessSummary",
    "MilitaryContact",
    "SatellitePassRecord",
    "SituationBriefResult",
    "TerrainHeightRecord",
    "ThermalHotspotRecord",
    "VesselRecord",
    "VesselTrackRecord",
    "WeatherMapResult",
    "WeatherResult",
]
