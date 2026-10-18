"""Slotted and frozen spatial telemetry and observation data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass(slots=True, frozen=True)
class FlightRecord:
    """Real-time aviation transponder record."""

    icao24: str
    lat: float
    lon: float
    callsign: str | None = None
    origin_country: str = "Unknown"
    altitude_m: float | None = None
    velocity_mps: float | None = None
    heading_deg: float | None = None
    vertical_rate_mps: float | None = None
    on_ground: bool = False
    military: bool = False
    operator: str | None = None
    aircraft_class: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class VesselRecord:
    """Real-time maritime AIS vessel record."""

    mmsi: str
    lat: float
    lon: float
    name: str = "UNKNOWN"
    ship_type: str = "Unknown"
    speed_kts: float = 0.0
    course_deg: float = 0.0
    heading_deg: float | None = None
    nav_status: str = "Underway"
    destination: str | None = None
    length_m: float | None = None
    width_m: float | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class EarthquakeRecord:
    """Seismic telemetry event record from USGS."""

    event_id: str
    title: str
    magnitude: float
    place: str
    lat: float
    lon: float
    depth_km: float
    time_utc: str
    tsunami_alert: bool = False
    url: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class ThermalHotspotRecord:
    """NASA FIRMS satellite thermal anomaly / wildfire hotspot record."""

    lat: float
    lon: float
    brightness_kelvin: float = 300.0
    frp_mw: float = 0.0
    confidence: str = "nominal"
    satellite: str = "VIIRS_NOAA20"
    acquisition_date: str = ""
    daynight: str = "D"

    def __post_init__(self) -> None:
        if not self.acquisition_date:
            object.__setattr__(self, "acquisition_date", _utc_now_iso())

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class SatellitePassRecord:
    """Computed orbital overpass for a satellite over ground coordinates."""

    sat_name: str
    norad_id: int
    pass_start_utc: str
    pass_end_utc: str
    culmination_utc: str
    max_elevation_deg: float
    pass_duration_seconds: int
    is_visible: bool = True

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class MilitaryContact:
    """Identified military air, naval, or radar contact."""

    contact_id: str
    callsign_or_name: str
    domain: str
    lat: float
    lon: float
    altitude_or_speed: float = 0.0
    origin_country: str = "Unknown"
    platform_type: str = "Military Asset"
    distance_km: float = 0.0

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class MilitaryAwarenessSummary:
    """Military intelligence summary within a tactical corridor."""

    center_lat: float
    center_lon: float
    radius_km: float = 250.0
    status: str = "ok"
    total_contacts: int = 0
    air_contacts: list[MilitaryContact] = field(default_factory=list)
    maritime_contacts: list[MilitaryContact] = field(default_factory=list)
    nearest_installations: list[dict[str, Any]] = field(default_factory=list)
    threat_level: str = "low"

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class InfrastructureRecord:
    """Global critical infrastructure asset."""

    infra_type: str
    name: str
    lat: float | None = None
    lon: float | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    country: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class CycloneRecord:
    """Tropical cyclone or hurricane advisory."""

    id: str
    name: str
    lat: float
    lon: float
    classification: str = "Tropical Storm"
    basin: str = "Atlantic"
    wind_kt: float | None = None
    pressure_hpa: float | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump


@dataclass(slots=True, frozen=True)
class TerrainHeightRecord:
    """Elevation query point with surface altitude metrics."""

    lat: float
    lon: float
    elevation_m: float

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    to_dict = model_dump
