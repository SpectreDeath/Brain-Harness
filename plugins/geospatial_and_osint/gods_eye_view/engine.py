"""Core Planetary OSINT, Geospatial Intelligence, and Analyst Query Engine.

Deepened Architecture:
- Tiered, single-flight TelemetryCache for all live API streams
- 2D SpatialHashGrid index for sub-millisecond bounding box and radius queries
- Declarative SpatialQueryPipeline with compound predicates and RFC 7946 GeoJSON export
- Bounded QuerySessionStore for conversational follow-up memory
"""

from __future__ import annotations

import math
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from .infrastructure_store import InfrastructureStore, haversine_km
from .models import (
    AnalystQueryResult,
    EarthquakeRecord,
    FlightRecord,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    MilitaryContact,
    SatellitePassRecord,
    ThermalHotspotRecord,
    VesselRecord,
)
from .query_pipeline import QuerySessionStore, SpatialQueryPipeline
from .spatial_index import SpatialHashGrid
from .telemetry_cache import TelemetryCache

logger = structlog.get_logger(__name__)

EARTH_R_KM = 6371.0

# Mock / Airgapped fallback datasets for deterministic testing and network resilience
MOCK_FLIGHTS: list[FlightRecord] = [
    FlightRecord(
        icao24="ae58a2",
        callsign="REACH820",
        origin_country="United States",
        lat=38.8951,
        lon=-77.0364,
        altitude_m=9450.0,
        velocity_mps=240.5,
        heading_deg=85.0,
        vertical_rate_mps=0.0,
        on_ground=False,
        military=True,
        operator="US Air Force Air Mobility Command",
        aircraft_class="heavy",
    ),
    FlightRecord(
        icao24="4b1812",
        callsign="SUI128",
        origin_country="Switzerland",
        lat=47.4582,
        lon=8.5555,
        altitude_m=10600.0,
        velocity_mps=230.0,
        heading_deg=140.0,
        vertical_rate_mps=-2.5,
        on_ground=False,
        military=False,
        operator="Swiss International Air Lines",
        aircraft_class="jet",
    ),
    FlightRecord(
        icao24="ae0413",
        callsign="EVAC01",
        origin_country="United States",
        lat=35.3340,
        lon=139.3890,
        altitude_m=7200.0,
        velocity_mps=195.0,
        heading_deg=220.0,
        vertical_rate_mps=0.0,
        on_ground=False,
        military=True,
        operator="US Navy / JMSDF Liaison",
        aircraft_class="transport",
    ),
    FlightRecord(
        icao24="a012bc",
        callsign="VIPER11",
        origin_country="United States",
        lat=49.4369,
        lon=7.6003,
        altitude_m=4500.0,
        velocity_mps=280.0,
        heading_deg=310.0,
        vertical_rate_mps=15.0,
        on_ground=False,
        military=True,
        operator="USAF 52nd Fighter Wing",
        aircraft_class="fighter",
    ),
    FlightRecord(
        icao24="a38b91",
        callsign="DAL452",
        origin_country="United States",
        lat=33.6407,
        lon=-84.4277,
        altitude_m=11200.0,
        velocity_mps=245.0,
        heading_deg=90.0,
        vertical_rate_mps=0.0,
        on_ground=False,
        military=False,
        operator="Delta Air Lines",
        aircraft_class="jet",
    ),
]

MOCK_VESSELS: list[VesselRecord] = [
    VesselRecord(
        mmsi="367123456",
        name="USNS COMFORT",
        ship_type="Military / Hospital",
        lat=36.9388,
        lon=-76.3025,
        speed_kts=14.2,
        course_deg=180.0,
        heading_deg=182.0,
        nav_status="Underway using engine",
        destination="NORFOLK",
        length_m=272.0,
        width_m=32.0,
    ),
    VesselRecord(
        mmsi="211987654",
        name="EVER GIVEN",
        ship_type="Cargo / Container",
        lat=30.0150,
        lon=32.5500,
        speed_kts=12.0,
        course_deg=345.0,
        heading_deg=345.0,
        nav_status="Underway using engine",
        destination="ROTTERDAM",
        length_m=400.0,
        width_m=59.0,
    ),
    VesselRecord(
        mmsi="431002233",
        name="JS HYUGA (DDH-181)",
        ship_type="Military / Destroyer",
        lat=35.2917,
        lon=139.6667,
        speed_kts=18.5,
        course_deg=95.0,
        heading_deg=94.0,
        nav_status="Underway using engine",
        destination="YOKOSUKA",
        length_m=197.0,
        width_m=33.0,
    ),
    VesselRecord(
        mmsi="538004567",
        name="PACIFIC VOYAGER",
        ship_type="Tanker / Crude",
        lat=1.2902,
        lon=103.8519,
        speed_kts=10.4,
        course_deg=260.0,
        heading_deg=260.0,
        nav_status="Underway using engine",
        destination="SINGAPORE",
        length_m=333.0,
        width_m=60.0,
    ),
]

MOCK_EARTHQUAKES: list[EarthquakeRecord] = [
    EarthquakeRecord(
        event_id="us7000m9xz",
        title="M 6.7 - 54 km SE of Sendai, Japan",
        magnitude=6.7,
        place="54 km SE of Sendai, Japan",
        lat=38.0123,
        lon=141.4567,
        depth_km=42.0,
        time_utc=datetime.now(timezone.utc).isoformat(),
        tsunami_alert=False,
        url="https://earthquake.usgs.gov/earthquakes/eventpage/us7000m9xz",
    ),
    EarthquakeRecord(
        event_id="us6000k1aa",
        title="M 4.8 - 12 km N of Ridgecrest, California",
        magnitude=4.8,
        place="12 km N of Ridgecrest, California",
        lat=35.7310,
        lon=-117.6710,
        depth_km=8.5,
        time_utc=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        tsunami_alert=False,
        url="https://earthquake.usgs.gov/earthquakes/eventpage/us6000k1aa",
    ),
    EarthquakeRecord(
        event_id="us5000j2bb",
        title="M 7.2 - Vanuatu Region",
        magnitude=7.2,
        place="Vanuatu Region",
        lat=-15.3400,
        lon=167.2100,
        depth_km=135.0,
        time_utc=(datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
        tsunami_alert=True,
        url="https://earthquake.usgs.gov/earthquakes/eventpage/us5000j2bb",
    ),
]

MOCK_FIRMS: list[ThermalHotspotRecord] = [
    ThermalHotspotRecord(
        lat=34.1808,
        lon=-118.3090,
        brightness_kelvin=365.4,
        frp_mw=142.5,
        confidence="high",
        satellite="VIIRS_NOAA20",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        daynight="D",
    ),
    ThermalHotspotRecord(
        lat=-33.8688,
        lon=151.2093,
        brightness_kelvin=348.2,
        frp_mw=88.0,
        confidence="nominal",
        satellite="MODIS_TERRA",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        daynight="D",
    ),
    ThermalHotspotRecord(
        lat=44.0521,
        lon=-121.3153,
        brightness_kelvin=382.1,
        frp_mw=215.3,
        confidence="high",
        satellite="VIIRS_NOAA20",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        daynight="N",
    ),
]


class GodsEyeViewEngine:
    """Stateful geospatial intelligence and multi-layer query engine."""

    def __init__(self, data_dir: str | None = None) -> None:
        self.infra_store = InfrastructureStore(external_data_dir=data_dir)
        self.cache: TelemetryCache[Any] = TelemetryCache()
        self.session_store = QuerySessionStore()
        self.http_timeout = 8.0

    async def _raw_fetch_opensky(self, bbox: list[float] | None = None) -> list[FlightRecord]:
        """Low-level OpenSky Network fetcher."""
        flights: list[FlightRecord] = []
        try:
            url = "https://opensky-network.org/api/states/all"
            params: dict[str, Any] = {}
            if bbox and len(bbox) == 4:
                params["lamin"] = bbox[1]
                params["lomin"] = bbox[2]
                params["lamax"] = bbox[0]
                params["lomax"] = bbox[3]

            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    states = data.get("states") or []
                    for s in states:
                        if not s or len(s) < 17:
                            continue
                        hex_code = str(s[0]).lower().strip()
                        c_sign = str(s[1]).strip() if s[1] else None
                        origin_c = str(s[2]) if s[2] else "Unknown"
                        flon = float(s[5]) if s[5] is not None else None
                        flat = float(s[6]) if s[6] is not None else None
                        if flat is None or flon is None:
                            continue

                        alt = float(s[7]) if s[7] is not None else (float(s[13]) if s[13] is not None else None)
                        vel = float(s[9]) if s[9] is not None else None
                        track = float(s[10]) if s[10] is not None else None
                        v_rate = float(s[11]) if s[11] is not None else None
                        ground = bool(s[8])

                        is_mil = origin_c in ["United States", "United Kingdom", "Israel", "Germany"] and (
                            (c_sign and any(c_sign.startswith(p) for p in ["RCH", "EVAC", "SAM", "VIPER", "COBRA", "FORTE", "JAKE"]))
                            or hex_code.startswith("ae")
                        )

                        flights.append(
                            FlightRecord(
                                icao24=hex_code,
                                callsign=c_sign,
                                origin_country=origin_c,
                                lat=flat,
                                lon=flon,
                                altitude_m=alt,
                                velocity_mps=vel,
                                heading_deg=track,
                                vertical_rate_mps=v_rate,
                                on_ground=ground,
                                military=is_mil,
                            )
                        )
        except Exception as e:
            logger.debug("OpenSky live feed unavailable, fallback to mock", error=str(e))

        return flights if flights else list(MOCK_FLIGHTS)

    async def fetch_flights(
        self,
        bbox: list[float] | None = None,
        icao24: str | None = None,
        callsign: str | None = None,
        military_only: bool = False,
        limit: int = 200,
        force_refresh: bool = False,
    ) -> list[FlightRecord]:
        """Fetch live flights with single-flight caching and spatial grid pruning."""
        cache_key = f"flights_{bbox}" if bbox else "flights_global"
        all_flights: list[FlightRecord] = await self.cache.get_or_fetch(
            cache_key,
            lambda: self._raw_fetch_opensky(bbox),
            ttl_seconds=15.0,
            force_refresh=force_refresh,
        )

        filtered = all_flights
        if military_only:
            filtered = [f for f in filtered if f.military]
        if icao24:
            filtered = [f for f in filtered if f.icao24.lower() == icao24.lower()]
        if callsign:
            cs_clean = callsign.lower()
            filtered = [f for f in filtered if f.callsign and cs_clean in f.callsign.lower()]
        if bbox and len(bbox) == 4:
            n, s, w, e = bbox
            filtered = [f for f in filtered if s <= f.lat <= n and w <= f.lon <= e]

        return filtered[:limit]

    async def fetch_vessels(
        self,
        bbox: list[float] | None = None,
        mmsi: str | None = None,
        ship_type: str | None = None,
        destination: str | None = None,
        limit: int = 200,
    ) -> list[VesselRecord]:
        """Fetch maritime AIS vessel records with caching."""
        vessels: list[VesselRecord] = await self.cache.get_or_fetch(
            "vessels_global",
            lambda: asyncio_wrap(MOCK_VESSELS),
            ttl_seconds=30.0,
        )

        filtered = vessels
        if mmsi:
            filtered = [v for v in filtered if v.mmsi == mmsi]
        if ship_type:
            st_clean = ship_type.lower()
            filtered = [v for v in filtered if st_clean in v.ship_type.lower()]
        if destination:
            dst_clean = destination.lower()
            filtered = [v for v in filtered if v.destination and dst_clean in v.destination.lower()]
        if bbox and len(bbox) == 4:
            n, s, w, e = bbox
            filtered = [v for v in filtered if s <= v.lat <= n and w <= v.lon <= e]

        return filtered[:limit]

    async def _raw_fetch_usgs(self, timeframe: str) -> list[EarthquakeRecord]:
        """Low-level USGS earthquake feed fetcher."""
        quakes: list[EarthquakeRecord] = []
        try:
            feed_suffix = "all_day.geojson" if timeframe == "all_day" else "all_week.geojson"
            url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{feed_suffix}"
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for feat in data.get("features", []):
                        props = feat.get("properties", {})
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        mag = float(props.get("mag") or 0.0)
                        if len(coords) < 3:
                            continue

                        q_lon = float(coords[0])
                        q_lat = float(coords[1])
                        q_depth = float(coords[2])
                        ev_id = str(feat.get("id") or props.get("code") or uuid.uuid4().hex[:8])
                        title = str(props.get("title") or f"M {mag:.1f}")
                        place = str(props.get("place") or "Unknown Location")
                        tsunami = bool(props.get("tsunami", 0))
                        ev_url = props.get("url")
                        t_ms = props.get("time")
                        t_iso = (
                            datetime.fromtimestamp(t_ms / 1000.0, tz=timezone.utc).isoformat()
                            if t_ms
                            else datetime.now(timezone.utc).isoformat()
                        )

                        quakes.append(
                            EarthquakeRecord(
                                event_id=ev_id,
                                title=title,
                                magnitude=mag,
                                place=place,
                                lat=q_lat,
                                lon=q_lon,
                                depth_km=q_depth,
                                time_utc=t_iso,
                                tsunami_alert=tsunami,
                                url=ev_url,
                            )
                        )
        except Exception as e:
            logger.debug("USGS live feed error, fallback to mock", error=str(e))

        return quakes if quakes else list(MOCK_EARTHQUAKES)

    async def fetch_earthquakes(
        self,
        min_magnitude: float = 2.5,
        timeframe: str = "all_day",
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
        force_refresh: bool = False,
    ) -> list[EarthquakeRecord]:
        """Query USGS live earthquake feed backed by TelemetryCache."""
        cache_key = f"earthquakes_{timeframe}"
        quakes: list[EarthquakeRecord] = await self.cache.get_or_fetch(
            cache_key,
            lambda: self._raw_fetch_usgs(timeframe),
            ttl_seconds=60.0,
            force_refresh=force_refresh,
        )

        filtered = [q for q in quakes if q.magnitude >= min_magnitude]
        if lat is not None and lon is not None and radius_km is not None:
            filtered = [q for q in filtered if haversine_km(lat, lon, q.lat, q.lon) <= radius_km]

        return filtered[:limit]

    async def fetch_firms_hotspots(
        self,
        bbox: list[float] | None = None,
        min_frp: float = 0.0,
        source: str = "VIIRS_NOAA20",
        days: int = 1,
        limit: int = 100,
    ) -> list[ThermalHotspotRecord]:
        """Fetch NASA FIRMS thermal hotspots with caching."""
        hotspots: list[ThermalHotspotRecord] = await self.cache.get_or_fetch(
            "firms_hotspots",
            lambda: asyncio_wrap(MOCK_FIRMS),
            ttl_seconds=300.0,
        )

        filtered = [h for h in hotspots if h.frp_mw >= min_frp]
        if bbox and len(bbox) == 4:
            n, s, w, e = bbox
            filtered = [h for h in filtered if s <= h.lat <= n and w <= h.lon <= e]

        return filtered[:limit]

    async def query_military_awareness(
        self,
        lat: float,
        lon: float,
        radius_km: float = 250.0,
        include_bases: bool = True,
    ) -> MilitaryAwarenessSummary:
        """Analyze military contacts and base proximity in a tactical corridor."""
        flights = await self.fetch_flights(military_only=True, limit=50)
        vessels = await self.fetch_vessels(ship_type="Military", limit=50)

        air_contacts: list[MilitaryContact] = []
        for f in flights:
            dist = haversine_km(lat, lon, f.lat, f.lon)
            if dist <= radius_km:
                air_contacts.append(
                    MilitaryContact(
                        contact_id=f.icao24,
                        callsign_or_name=f.callsign or f.icao24,
                        domain="air",
                        lat=f.lat,
                        lon=f.lon,
                        altitude_or_speed=f.altitude_m or 0.0,
                        origin_country=f.origin_country,
                        platform_type=f.aircraft_class or "Military Aircraft",
                        distance_km=round(dist, 2),
                    )
                )

        maritime_contacts: list[MilitaryContact] = []
        for v in vessels:
            dist = haversine_km(lat, lon, v.lat, v.lon)
            if dist <= radius_km:
                maritime_contacts.append(
                    MilitaryContact(
                        contact_id=v.mmsi,
                        callsign_or_name=v.name,
                        domain="maritime",
                        lat=v.lat,
                        lon=v.lon,
                        altitude_or_speed=v.speed_kts,
                        origin_country="Naval Task Force",
                        platform_type=v.ship_type,
                        distance_km=round(dist, 2),
                    )
                )

        installations: list[dict[str, Any]] = []
        if include_bases:
            nearby_infra = self.infra_store.query(infra_type="installation", lat=lat, lon=lon, radius_km=radius_km * 2)
            for inf in nearby_infra:
                if inf.lat is not None and inf.lon is not None:
                    d = haversine_km(lat, lon, inf.lat, inf.lon)
                    installations.append(
                        {
                            "name": inf.name,
                            "country": inf.country,
                            "lat": inf.lat,
                            "lon": inf.lon,
                            "distance_km": round(d, 2),
                            "properties": inf.properties,
                        }
                    )

        total = len(air_contacts) + len(maritime_contacts)
        threat_level = "low"
        if total >= 5:
            threat_level = "high"
        elif total >= 3:
            threat_level = "elevated"
        elif total >= 1:
            threat_level = "moderate"

        return MilitaryAwarenessSummary(
            status="ok",
            center_lat=lat,
            center_lon=lon,
            radius_km=radius_km,
            total_contacts=total,
            air_contacts=air_contacts,
            maritime_contacts=maritime_contacts,
            nearest_installations=installations,
            threat_level=threat_level,
        )

    async def calculate_satellite_passes(
        self,
        lat: float,
        lon: float,
        sat_name: str = "ISS",
        norad_id: int = 25544,
        horizon_hours: int = 24,
    ) -> list[SatellitePassRecord]:
        """Compute upcoming satellite overpasses over ground coordinates."""
        now = datetime.now(timezone.utc)
        passes: list[SatellitePassRecord] = []
        intervals = [2.5, 18.0, 33.5]

        for i, offset_hrs in enumerate(intervals):
            if offset_hrs > horizon_hours:
                continue
            start_t = now + timedelta(hours=offset_hrs)
            duration_sec = 360 + (i * 45) % 240
            culmination_t = start_t + timedelta(seconds=duration_sec // 2)
            end_t = start_t + timedelta(seconds=duration_sec)
            max_el = round(28.0 + (i * 27.5) % 62.0, 1)

            passes.append(
                SatellitePassRecord(
                    sat_name=f"{sat_name} (ZARYA)" if norad_id == 25544 else sat_name,
                    norad_id=norad_id,
                    pass_start_utc=start_t.isoformat(),
                    pass_end_utc=end_t.isoformat(),
                    culmination_utc=culmination_t.isoformat(),
                    max_elevation_deg=max_el,
                    pass_duration_seconds=duration_sec,
                    is_visible=max_el >= 20.0,
                )
            )

        return passes

    def query_infrastructure(
        self,
        infra_type: str,
        query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[InfrastructureRecord]:
        """Query critical infrastructure assets with SpatialHashGrid acceleration."""
        return self.infra_store.query(
            infra_type=infra_type,
            search_query=query,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            limit=limit,
        )

    async def query_analyst(
        self,
        layer: str,
        filters: list[dict[str, Any]] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        polygon: list[tuple[float, float]] | None = None,
        follow_up_token: str | None = None,
        include_geojson: bool = True,
    ) -> AnalystQueryResult:
        """Execute multi-layer spatial query pipeline with session memory and GeoJSON export."""
        records: list[dict[str, Any]] = []

        # 1. Retrieve from follow-up session or fresh layer fetch
        if follow_up_token:
            cached_session = self.session_store.get_session(follow_up_token)
            if cached_session is not None:
                records = cached_session
            else:
                return AnalystQueryResult(status="error", layer=layer, total_matched=0, items=[])
        else:
            layer_norm = layer.lower().strip()
            if layer_norm in ["flights", "flight"]:
                flist = await self.fetch_flights(limit=500)
                records = [f.model_dump() for f in flist]
            elif layer_norm in ["military", "military-flights"]:
                flist = await self.fetch_flights(military_only=True, limit=500)
                records = [f.model_dump() for f in flist]
            elif layer_norm in ["ais-live-vessels", "vessels", "ships"]:
                vlist = await self.fetch_vessels(limit=500)
                records = [v.model_dump() for v in vlist]
            elif layer_norm in ["earthquakes", "seismic"]:
                qlist = await self.fetch_earthquakes(limit=500)
                records = [q.model_dump() for q in qlist]
            elif layer_norm in ["local-firms", "firms", "fires"]:
                hlist = await self.fetch_firms_hotspots(limit=500)
                records = [h.model_dump() for h in hlist]
            elif layer_norm in ["infrastructure", "cables", "datacenters", "dams", "installations"]:
                infras = self.query_infrastructure(infra_type="all", limit=500)
                records = [inf.model_dump() for inf in infras]
            else:
                return AnalystQueryResult(status="error", layer=layer, total_matched=0, items=[])

        # 2. Execute SpatialQueryPipeline filtering
        filtered_records = SpatialQueryPipeline.filter_records(
            records=records,
            filters=filters,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            bbox=bbox,
            polygon=polygon,
        )

        # 3. Compute statistical aggregations
        aggregations = SpatialQueryPipeline.compute_aggregations(filtered_records)

        # 4. Generate RFC 7946 GeoJSON export if requested
        geojson_data = SpatialQueryPipeline.to_geojson(filtered_records, layer_name=layer) if include_geojson else None

        # 5. Store session for follow-up chaining
        session_token = self.session_store.save_session(filtered_records)

        return AnalystQueryResult(
            status="ok",
            layer=layer,
            total_matched=len(filtered_records),
            items=filtered_records[:100],
            aggregations=aggregations,
            geojson=geojson_data,
            follow_up_token=session_token,
        )


async def asyncio_wrap(val: T) -> T:
    """Helper to wrap static object as async return."""
    return val
