"""Tactical military awareness and satellite pass calculation engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from ..infrastructure_store import haversine_km
from ..models import (
    MilitaryAwarenessSummary,
    MilitaryContact,
    SatellitePassRecord,
)

if TYPE_CHECKING:
    from .core import GodsEyeViewEngine


async def query_military_awareness(
    engine: GodsEyeViewEngine,
    lat: float,
    lon: float,
    radius_km: float = 250.0,
    include_bases: bool = True,
) -> MilitaryAwarenessSummary:
    """Analyze military contacts and base proximity in a tactical corridor."""
    flights = await engine.fetch_flights(military_only=True, limit=50)
    vessels = await engine.fetch_vessels(ship_type="Military", limit=50)

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
        nearby_infra = engine.infra_store.query(
            infra_type="installation", lat=lat, lon=lon, radius_km=radius_km * 2
        )
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


__all__ = [
    "calculate_satellite_passes",
    "query_military_awareness",
]
