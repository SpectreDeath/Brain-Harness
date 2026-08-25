"""Pydantic v2 data models for God's Eye View plugin entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlightRecord(BaseModel):
    """Real-time aviation transponder record."""

    icao24: str = Field(..., description="Unique 24-bit ICAO transponder address in hex")
    callsign: str | None = Field(default=None, description="Radiotelephony callsign or flight number")
    origin_country: str = Field(default="Unknown", description="Country of aircraft registration")
    lat: float = Field(..., description="WGS-84 latitude in decimal degrees")
    lon: float = Field(..., description="WGS-84 longitude in decimal degrees")
    altitude_m: float | None = Field(default=None, description="Barometric or geometric altitude in meters")
    velocity_mps: float | None = Field(default=None, description="Ground speed in meters per second")
    heading_deg: float | None = Field(default=None, description="True track in degrees clockwise from north")
    vertical_rate_mps: float | None = Field(default=None, description="Vertical speed in m/s")
    on_ground: bool = Field(default=False, description="Whether aircraft is reporting on ground")
    military: bool = Field(default=False, description="Whether aircraft is identified as military or government")
    operator: str | None = Field(default=None, description="Operating airline or military branch")
    aircraft_class: str | None = Field(default=None, description="Aircraft class or category")


class VesselRecord(BaseModel):
    """Real-time maritime AIS vessel record."""

    mmsi: str = Field(..., description="Maritime Mobile Service Identity (MMSI)")
    name: str = Field(default="UNKNOWN", description="Vessel name")
    ship_type: str = Field(default="Unknown", description="Vessel classification")
    lat: float = Field(..., description="WGS-84 latitude in decimal degrees")
    lon: float = Field(..., description="WGS-84 longitude in decimal degrees")
    speed_kts: float = Field(default=0.0, description="Speed over ground in knots")
    course_deg: float = Field(default=0.0, description="Course over ground in degrees")
    heading_deg: float | None = Field(default=None, description="True heading in degrees")
    nav_status: str = Field(default="Underway", description="Navigation status")
    destination: str | None = Field(default=None, description="Reported destination port")
    length_m: float | None = Field(default=None, description="Vessel length in meters")
    width_m: float | None = Field(default=None, description="Vessel beam in meters")


class EarthquakeRecord(BaseModel):
    """Seismic telemetry event record from USGS."""

    event_id: str = Field(..., description="USGS seismic event identifier")
    title: str = Field(..., description="Descriptive event title")
    magnitude: float = Field(..., description="Moment magnitude")
    place: str = Field(..., description="Geographic location description")
    lat: float = Field(..., description="Epicenter latitude")
    lon: float = Field(..., description="Epicenter longitude")
    depth_km: float = Field(..., description="Hypocenter depth in kilometers")
    time_utc: str = Field(..., description="UTC timestamp of seismic occurrence")
    tsunami_alert: bool = Field(default=False, description="Whether event triggered a tsunami alert")
    url: str | None = Field(default=None, description="Link to USGS event page")


class ThermalHotspotRecord(BaseModel):
    """NASA FIRMS satellite thermal anomaly record."""

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    brightness_kelvin: float = Field(default=300.0, description="Thermal infrared brightness temperature in Kelvin")
    frp_mw: float = Field(default=0.0, description="Fire Radiative Power in Megawatts (MW)")
    confidence: str = Field(default="nominal", description="Detection confidence")
    satellite: str = Field(default="VIIRS_NOAA20", description="Observing instrument/platform")
    acquisition_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"), description="UTC acquisition date")
    daynight: str = Field(default="D", description="Day ('D') or Night ('N') observation")


class SatellitePassRecord(BaseModel):
    """Computed orbital overpass for a satellite over ground coordinates."""

    sat_name: str = Field(..., description="Satellite name")
    norad_id: int = Field(..., description="NORAD Catalog Number")
    pass_start_utc: str = Field(..., description="Pass AOS UTC timestamp")
    pass_end_utc: str = Field(..., description="Pass LOS UTC timestamp")
    culmination_utc: str = Field(..., description="Time of peak elevation")
    max_elevation_deg: float = Field(..., description="Peak elevation angle in degrees above horizon")
    pass_duration_seconds: int = Field(..., description="Duration in seconds")
    is_visible: bool = Field(default=True, description="Whether pass is optically visible")


class MilitaryContact(BaseModel):
    """Identified military air, naval, or radar contact."""

    contact_id: str = Field(..., description="Identifier (ICAO24 or MMSI)")
    callsign_or_name: str = Field(..., description="Callsign or vessel designation")
    domain: str = Field(..., description="Domain: 'air' or 'maritime'")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    altitude_or_speed: float = Field(default=0.0, description="Altitude (m) or speed (kts)")
    origin_country: str = Field(default="Unknown", description="Country / military branch")
    platform_type: str = Field(default="Military Asset", description="Detected platform type")
    distance_km: float = Field(..., description="Distance to reference point in km")


class MilitaryAwarenessSummary(BaseModel):
    """Military intelligence summary within a tactical corridor."""

    status: str = Field(default="ok", description="Status code")
    center_lat: float = Field(..., description="Center latitude")
    center_lon: float = Field(..., description="Center longitude")
    radius_km: float = Field(..., description="Analysis radius in km")
    total_contacts: int = Field(default=0, description="Total military contacts detected")
    air_contacts: list[MilitaryContact] = Field(default_factory=list, description="Airborne military assets")
    maritime_contacts: list[MilitaryContact] = Field(default_factory=list, description="Naval military vessels")
    nearest_installations: list[dict[str, Any]] = Field(default_factory=list, description="Airbases and radar installations")
    threat_level: str = Field(default="low", description="Corridor threat level: low, moderate, elevated, high")


class InfrastructureRecord(BaseModel):
    """Global critical infrastructure asset."""

    infra_type: str = Field(..., description="Type: 'submarine_cable', 'landing_point', 'datacenter', 'dam'")
    name: str = Field(..., description="Name of infrastructure asset")
    lat: float | None = Field(default=None, description="Representative latitude coordinate")
    lon: float | None = Field(default=None, description="Representative longitude coordinate")
    properties: dict[str, Any] = Field(default_factory=dict, description="Metadata properties")
    country: str | None = Field(default=None, description="Country or territory jurisdiction")


class AnalystQueryResult(BaseModel):
    """Result of multi-layer spatial query engine execution."""

    status: str = Field(default="ok", description="Status indicator")
    layer: str = Field(..., description="Target query layer")
    total_matched: int = Field(default=0, description="Total matching records")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Matching entity records")
    aggregations: dict[str, Any] = Field(default_factory=dict, description="Computed summary statistics")
    follow_up_token: str | None = Field(default=None, description="Token to reference in follow-up queries")


class ImageryRenderResult(BaseModel):
    """Result of geospatial imagery generation or 3D rendering."""

    status: str = Field(default="ok", description="Status indicator")
    tool_name: str = Field(..., description="Tool that generated output")
    output_path: str = Field(..., description="Absolute file path to generated image asset")
    format: str = Field(default="png", description="Image format")
    dimensions: list[int] = Field(default_factory=lambda: [2048, 2048], description="[width, height] in pixels")
    gsd_m_per_px: float | None = Field(default=None, description="Ground Sample Distance in m/px")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional rendering metadata")
