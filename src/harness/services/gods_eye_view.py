"""God's Eye View Planetary OSINT & Spatial Intelligence service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FlightRecord(BaseModel):
    """Real-time aviation transponder record."""

    icao24: str = Field(..., description="Unique 24-bit ICAO transponder address in hex")
    callsign: str | None = Field(default=None, description="Radiotelephony callsign or flight number")
    origin_country: str = Field(default="Unknown", description="Country of aircraft registration")
    lat: float = Field(..., description="WGS-84 latitude in decimal degrees")
    lon: float = Field(..., description="WGS-84 longitude in decimal degrees")
    altitude_m: float | None = Field(default=None, description="Barometric or geometric altitude in meters")
    velocity_mps: float | None = Field(default=None, description="Ground speed in meters per second")
    heading_deg: float | None = Field(default=None, description="True track in degrees clock-wise from north")
    vertical_rate_mps: float | None = Field(default=None, description="Vertical speed in m/s")
    on_ground: bool = Field(default=False, description="Whether aircraft is reporting on ground")
    military: bool = Field(default=False, description="Whether aircraft is identified as military or government")
    operator: str | None = Field(default=None, description="Operating airline or military branch")
    aircraft_class: str | None = Field(default=None, description="Aircraft class or category (e.g., jet, heavy, helicopter, fighter)")


class VesselRecord(BaseModel):
    """Real-time maritime AIS vessel record."""

    mmsi: str = Field(..., description="Maritime Mobile Service Identity (MMSI)")
    name: str = Field(default="UNKNOWN", description="Vessel name")
    ship_type: str = Field(default="Unknown", description="Vessel classification (Cargo, Tanker, Military, Fishing, etc.)")
    lat: float = Field(..., description="WGS-84 latitude in decimal degrees")
    lon: float = Field(..., description="WGS-84 longitude in decimal degrees")
    speed_kts: float = Field(default=0.0, description="Speed over ground in knots")
    course_deg: float = Field(default=0.0, description="Course over ground in degrees")
    heading_deg: float | None = Field(default=None, description="True heading in degrees")
    nav_status: str = Field(default="Underway", description="Navigation status (e.g. Underway using engine, At anchor)")
    destination: str | None = Field(default=None, description="Reported destination port")
    length_m: float | None = Field(default=None, description="Vessel overall length in meters")
    width_m: float | None = Field(default=None, description="Vessel overall beam in meters")


class EarthquakeRecord(BaseModel):
    """Seismic telemetry event record from USGS."""

    event_id: str = Field(..., description="USGS seismic event identifier")
    title: str = Field(..., description="Descriptive event title (e.g. M 6.2 - 24 km SE of Tokyo)")
    magnitude: float = Field(..., description="Moment magnitude (Mw or mb)")
    place: str = Field(..., description="Geographic location description")
    lat: float = Field(..., description="Epicenter latitude in decimal degrees")
    lon: float = Field(..., description="Epicenter longitude in decimal degrees")
    depth_km: float = Field(..., description="Hypocenter depth in kilometers")
    time_utc: str = Field(..., description="UTC ISO-8601 timestamp of seismic occurrence")
    tsunami_alert: bool = Field(default=False, description="Whether event triggered a tsunami alert flag")
    url: str | None = Field(default=None, description="Link to USGS event detail page")


class ThermalHotspotRecord(BaseModel):
    """NASA FIRMS satellite thermal anomaly / wildfire hotspot record."""

    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    brightness_kelvin: float = Field(default=300.0, description="Thermal infrared brightness temperature in Kelvin")
    frp_mw: float = Field(default=0.0, description="Fire Radiative Power in Megawatts (MW)")
    confidence: str = Field(default="nominal", description="Detection confidence (low, nominal, high)")
    satellite: str = Field(default="VIIRS_NOAA20", description="Observing instrument/satellite platform")
    acquisition_date: str = Field(default_factory=lambda: _utc_now().strftime("%Y-%m-%d"), description="UTC acquisition date")
    daynight: str = Field(default="D", description="Day ('D') or Night ('N') observation")


class SatellitePassRecord(BaseModel):
    """Computed orbital overpass for a satellite over ground coordinates."""

    sat_name: str = Field(..., description="Satellite name (e.g. ISS (ZARYA), STARLINK-1007)")
    norad_id: int = Field(..., description="NORAD Catalog Number")
    pass_start_utc: str = Field(..., description="Pass acquisition of signal (AOS) UTC timestamp")
    pass_end_utc: str = Field(..., description="Pass loss of signal (LOS) UTC timestamp")
    culmination_utc: str = Field(..., description="Time of maximum elevation / closest approach")
    max_elevation_deg: float = Field(..., description="Peak elevation angle in degrees above horizon")
    pass_duration_seconds: int = Field(..., description="Total visible duration of overpass in seconds")
    is_visible: bool = Field(default=True, description="Whether pass occurs during optical illumination window")


class MilitaryContact(BaseModel):
    """Identified military air, naval, or radar contact."""

    contact_id: str = Field(..., description="Identifier (ICAO24 or MMSI)")
    callsign_or_name: str = Field(..., description="Callsign or vessel designation")
    domain: str = Field(..., description="Domain: 'air' or 'maritime'")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    altitude_or_speed: float = Field(default=0.0, description="Altitude (m) for air or speed (kts) for naval")
    origin_country: str = Field(default="Unknown", description="Identified country / military force")
    platform_type: str = Field(default="Military Asset", description="Detected platform type (Fighter, Tanker, Destroyer)")
    distance_km: float = Field(..., description="Distance to reference vantage point in km")


class MilitaryAwarenessSummary(BaseModel):
    """Military intelligence summary within a tactical corridor."""

    status: str = Field(default="ok", description="Status code")
    center_lat: float = Field(..., description="Center latitude")
    center_lon: float = Field(..., description="Center longitude")
    radius_km: float = Field(..., description="Analysis radius in km")
    total_contacts: int = Field(default=0, description="Total military contacts detected")
    air_contacts: list[MilitaryContact] = Field(default_factory=list, description="Airborne military assets")
    maritime_contacts: list[MilitaryContact] = Field(default_factory=list, description="Naval military vessels")
    nearest_installations: list[dict[str, Any]] = Field(default_factory=list, description="Proximity to airbases and radar installations")
    threat_level: str = Field(default="low", description="Evaluated corridor activity level: low, moderate, elevated, high")


class InfrastructureRecord(BaseModel):
    """Global critical infrastructure asset (submarine cable, landing point, datacenter, dam)."""

    infra_type: str = Field(..., description="Type: 'submarine_cable', 'landing_point', 'datacenter', 'dam'")
    name: str = Field(..., description="Name of infrastructure asset")
    lat: float | None = Field(default=None, description="Representative latitude coordinate")
    lon: float | None = Field(default=None, description="Representative longitude coordinate")
    properties: dict[str, Any] = Field(default_factory=dict, description="Metadata properties (owners, capacity, voltage)")
    country: str | None = Field(default=None, description="Country or territory jurisdiction")


class AnalystQueryResult(BaseModel):
    """Result of multi-layer spatial query engine execution."""

    status: str = Field(default="ok", description="Status indicator")
    layer: str = Field(..., description="Target query layer ('flights', 'military', 'ais-live-vessels', 'local-firms', 'earthquakes', 'infrastructure')")
    total_matched: int = Field(default=0, description="Total matching records")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Matching entity records")
    aggregations: dict[str, Any] = Field(default_factory=dict, description="Computed summary statistics (count, min, max, avg)")
    follow_up_token: str | None = Field(default=None, description="Token to reference this result set in follow-up queries")


class ImageryRenderResult(BaseModel):
    """Result of geospatial imagery generation or 3D rendering."""

    status: str = Field(default="ok", description="Status indicator")
    tool_name: str = Field(..., description="Tool that generated output (sat-ortho, streetview-headings, cesium-render)")
    output_path: str = Field(..., description="Absolute file path to generated image asset")
    format: str = Field(default="png", description="Image format (png, jpg, webp)")
    dimensions: list[int] = Field(default_factory=lambda: [2048, 2048], description="[width, height] in pixels")
    gsd_m_per_px: float | None = Field(default=None, description="Ground Sample Distance in meters per pixel if applicable")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional bounding box, heading, or rendering metadata")


@runtime_checkable
class GodsEyeViewService(Protocol):
    """Protocol for the God's Eye View Planetary Intelligence Service."""

    async def query_analyst(
        self,
        layer: str,
        filters: list[dict[str, Any]] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        follow_up_token: str | None = None,
    ) -> AnalystQueryResult:
        """Execute multi-layer spatial queries, compound filters, and aggregations."""
        ...

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
    ) -> list[FlightRecord]:
        """Fetch live aviation transponder vectors with OpenSky / ADSB-lol fallback."""
        ...

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        """Retrieve real-time maritime AIS vessel records."""
        ...

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[EarthquakeRecord]:
        """Query USGS live seismic telemetry."""
        ...

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS thermal hotspots and active wildfire perimeters."""
        ...

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        """Compute tactical military awareness corridor and air/naval assets."""
        ...

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        """Predict upcoming orbital overpasses over ground coordinates."""
        ...

    async def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[InfrastructureRecord]:
        """Query offline global submarine cables, datacenters, dams, and POIs."""
        ...

    async def render_sat_ortho(
        self,
        lat: float,
        lon: float,
        zoom: int = 21,
        size: int = 2048,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Stitch high-resolution satellite orthomosaic from 3D Map Tiles."""
        ...

    async def capture_streetview_headings(
        self,
        lat: float,
        lon: float,
        fov: int = 90,
        pitch: int = 0,
        neighbors: bool = False,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Capture 8 compass headings (360 ground view) via Static Street View."""
        ...

    async def render_globe_snapshot(
        self,
        lat: float,
        lon: float,
        altitude_m: float = 1000.0,
        pitch: float = -45.0,
        heading: float = 0.0,
        style: str = "normal",
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Render photorealistic 3D Cesium globe snapshots with post-processing shaders."""
        ...


GODS_EYE_VIEW_SERVICE_KEY: ServiceKey[GodsEyeViewService] = ServiceKey("service.gods_eye_view")
