"""Slotted and frozen imagery, query, and surveillance data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class AnalystQueryResult:
    """Result of multi-layer spatial query engine execution."""

    layer: str
    status: str = "ok"
    total_matched: int = 0
    items: list[dict[str, Any]] = field(default_factory=list)
    aggregations: dict[str, Any] = field(default_factory=dict)
    geojson: dict[str, Any] | None = None
    follow_up_token: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class ImageryRenderResult:
    """Result of geospatial imagery generation or 3D rendering."""

    tool_name: str
    output_path: str
    status: str = "ok"
    format: str = "png"
    dimensions: list[int] = field(default_factory=lambda: [2048, 2048])
    gsd_m_per_px: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class WeatherResult:
    """Current weather observations at target point."""

    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    location: dict[str, Any] = field(default_factory=dict)
    weather: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class WeatherMapResult:
    """Weather map radar/satellite product snapshot."""

    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    map_type: str = "radar"
    title: str = ""
    coverage: str = ""
    image_url_or_b64: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class CctvCameraRecord:
    """Public city or highway surveillance camera record."""

    lat: float
    lon: float
    id: str = ""
    camera_id: str | None = None
    name: str | None = None
    city: str | None = None
    provider: str | None = None
    heading_deg: float | None = None
    distance_km: float | None = None

    def __post_init__(self) -> None:
        if not self.id and self.camera_id:
            object.__setattr__(self, "id", self.camera_id)
        elif self.id and not self.camera_id:
            object.__setattr__(self, "camera_id", self.id)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class CctvSnapshotResult:
    """Still image frame from public camera feed."""

    camera_id: str
    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    summary: str = ""
    image_url_or_b64: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class AircraftTrackRecord:
    """Historical flight track position sequence."""

    icao24: str
    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    points: list[dict[str, Any]] = field(default_factory=list)
    total_points: int = 0
    summary: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class VesselTrackRecord:
    """Historical maritime vessel position trail."""

    mmsi: str
    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    points: list[dict[str, Any]] = field(default_factory=list)
    total_points: int = 0
    summary: str = ""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class SituationBriefResult:
    """Multi-domain situational awareness brief."""

    status: str = "ok"
    source: str = "mcp_live"
    is_live: bool = True
    area_label: str = ""
    summary_lines: list[str] = field(default_factory=list)
    sections: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump
