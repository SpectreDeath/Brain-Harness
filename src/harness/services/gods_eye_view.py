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


class WeatherResult(BaseModel):
    """Current weather observations at target point."""

    status: str = Field(default="ok", description="Status code")
    source: str = Field(default="mcp_live", description="Data provenance: 'mcp_live' or 'simulated_fallback'")
    is_live: bool = Field(default=True, description="Whether data came from live feed")
    location: dict[str, Any] = Field(default_factory=dict, description="Resolved geographic point")
    weather: dict[str, Any] = Field(default_factory=dict, description="Meteorological conditions")
    summary: str = Field(default="", description="Human-readable conditions summary")


class WeatherMapResult(BaseModel):
    """Weather map radar/satellite product snapshot."""

    status: str = Field(default="ok", description="Status code")
    source: str = Field(default="mcp_live", description="Data provenance: 'mcp_live' or 'simulated_fallback'")
    is_live: bool = Field(default=True, description="Whether data came from live feed")
    map_type: str = Field(default="radar", description="Product type (radar, satellite, lightning)")
    title: str = Field(default="", description="Product title")
    coverage: str = Field(default="", description="Coverage extent description")
    image_url_or_b64: str | None = Field(default=None, description="Image reference or encoded raster")


class CctvCameraRecord(BaseModel):
    """Public city or highway surveillance camera record."""

    id: str = Field(default="", description="Unique camera identifier")
    camera_id: str | None = Field(default=None, description="Camera identifier alias")
    name: str | None = Field(default=None, description="Camera display name")
    city: str | None = Field(default=None, description="City or jurisdiction")
    provider: str | None = Field(default=None, description="Operating agency or provider")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    heading_deg: float | None = Field(default=None, description="Camera viewing angle")
    distance_km: float | None = Field(default=None, description="Distance from search center")

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.camera_id:
            object.__setattr__(self, "id", self.camera_id)
        elif self.id and not self.camera_id:
            object.__setattr__(self, "camera_id", self.id)


class CctvSnapshotResult(BaseModel):
    """Still image frame from public camera feed."""

    status: str = Field(default="ok", description="Status indicator")
    source: str = Field(default="mcp_live", description="Data provenance")
    is_live: bool = Field(default=True, description="Live frame status")
    camera_id: str = Field(..., description="Camera identifier")
    summary: str = Field(default="", description="Camera summary caption")
    image_url_or_b64: str | None = Field(default=None, description="Snapshot raster data or link")


class AircraftTrackRecord(BaseModel):
    """Historical flight track position sequence."""

    status: str = Field(default="ok", description="Status code")
    source: str = Field(default="mcp_live", description="Data provenance")
    is_live: bool = Field(default=True, description="Live feed status")
    icao24: str = Field(..., description="ICAO24 transponder address")
    points: list[dict[str, Any]] = Field(default_factory=list, description="Ordered time-series points [time, lat, lon, alt]")
    total_points: int = Field(default=0, description="Total sampled track positions")
    summary: str = Field(default="", description="Track summary sentence")


class VesselTrackRecord(BaseModel):
    """Historical maritime vessel position trail."""

    status: str = Field(default="ok", description="Status code")
    source: str = Field(default="mcp_live", description="Data provenance")
    is_live: bool = Field(default=True, description="Live feed status")
    mmsi: str = Field(..., description="Maritime Mobile Service Identity")
    points: list[dict[str, Any]] = Field(default_factory=list, description="Chronological track points")
    total_points: int = Field(default=0, description="Total recorded positions")
    summary: str = Field(default="", description="Vessel track summary")


class CycloneRecord(BaseModel):
    """Tropical cyclone or hurricane advisory."""

    id: str = Field(..., description="Storm identifier")
    name: str = Field(..., description="Storm name")
    classification: str = Field(default="Tropical Storm", description="Classification (Hurricane, Typhoon, Depression)")
    basin: str = Field(default="Atlantic", description="Ocean basin")
    lat: float = Field(..., description="Current center latitude")
    lon: float = Field(..., description="Current center longitude")
    wind_kt: float | None = Field(default=None, description="Maximum sustained winds in knots")
    pressure_hpa: float | None = Field(default=None, description="Central pressure in hPa")


class TerrainHeightRecord(BaseModel):
    """Elevation query point with surface altitude metrics."""

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    elevation_m: float = Field(..., description="Height above mean sea level in meters")


class SituationBriefResult(BaseModel):
    """Multi-domain situational awareness brief."""

    status: str = Field(default="ok", description="Status indicator")
    source: str = Field(default="mcp_live", description="Data provenance")
    is_live: bool = Field(default=True, description="Live feed flag")
    area_label: str = Field(default="", description="Analyzed area description")
    summary_lines: list[str] = Field(default_factory=list, description="High-level bullet summaries")
    sections: dict[str, Any] = Field(default_factory=dict, description="Domain section responses (weather, flights, ships, hazards)")


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

    # Tier 2 Pass-Through Tools
    async def get_weather(
        self,
        place: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherResult:
        """Retrieve current weather conditions at point or named place."""
        ...

    async def get_weather_map(
        self,
        map_type: str = "radar",
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> WeatherMapResult:
        """Fetch precipitation radar or cloud satellite imagery overlay."""
        ...

    async def find_cctv_cameras(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 50,
    ) -> list[CctvCameraRecord]:
        """Search public camera installations in an area."""
        ...

    async def get_cctv_snapshot(
        self,
        camera_id: str,
    ) -> CctvSnapshotResult:
        """Retrieve latest still snapshot frame from public camera."""
        ...

    async def find_aircraft(
        self,
        callsign: str | None = None,
        icao24: str | None = None,
        registration: str | None = None,
        limit: int = 50,
    ) -> list[FlightRecord]:
        """Search aircraft globally by callsign, ICAO hex, or tail registration."""
        ...

    async def get_aircraft_track(
        self,
        icao24: str,
        military: bool = False,
    ) -> AircraftTrackRecord:
        """Fetch recent position history track for an aircraft."""
        ...

    async def find_vessel(
        self,
        mmsi: str | None = None,
        imo: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[VesselRecord]:
        """Search vessels globally by MMSI, IMO number, or vessel name."""
        ...

    async def get_vessel_track(
        self,
        mmsi: str,
    ) -> VesselTrackRecord:
        """Fetch recent position track history for an AIS vessel."""
        ...

    async def situation_brief(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> SituationBriefResult:
        """Generate composite multi-domain situation overview for an area."""
        ...

    async def get_terrain_height(
        self,
        points: list[dict[str, float]],
    ) -> list[TerrainHeightRecord]:
        """Query terrain ground elevation above sea level for coordinate points."""
        ...

    async def get_cyclones(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> list[CycloneRecord]:
        """Fetch active tropical cyclone and hurricane advisories."""
        ...

    async def get_active_fires(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS active fires in an area."""
        ...

    async def get_recent_imagery(
        self,
        place: str | None = None,
        bbox: list[float] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> dict[str, Any]:
        """Fetch recent Landsat/Sentinel/VIIRS optical satellite imagery metadata."""
        ...


GODS_EYE_VIEW_SERVICE_KEY: ServiceKey[GodsEyeViewService] = ServiceKey("service.gods_eye_view")
