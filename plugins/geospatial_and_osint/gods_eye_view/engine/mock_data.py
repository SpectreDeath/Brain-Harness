"""Mock datasets and constants for airgapped resilience and testing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TypeVar

from ..models import (
    EarthquakeRecord,
    FlightRecord,
    ThermalHotspotRecord,
    VesselRecord,
)

T = TypeVar("T")

EARTH_R_KM: float = 6371.0


async def asyncio_wrap(val: T) -> T:
    """Helper to wrap static object as async return."""
    return val


MOCK_FLIGHTS: list[FlightRecord] = [
    FlightRecord(
        icao24="ae58a2", callsign="REACH820", origin_country="United States",
        lat=38.8951, lon=-77.0364, altitude_m=9450.0, velocity_mps=240.5,
        heading_deg=85.0, vertical_rate_mps=0.0, on_ground=False, military=True,
        operator="US Air Force Air Mobility Command", aircraft_class="heavy",
    ),
    FlightRecord(
        icao24="4b1812", callsign="SUI128", origin_country="Switzerland",
        lat=47.4582, lon=8.5555, altitude_m=10600.0, velocity_mps=230.0,
        heading_deg=140.0, vertical_rate_mps=-2.5, on_ground=False, military=False,
        operator="Swiss International Air Lines", aircraft_class="jet",
    ),
    FlightRecord(
        icao24="ae0413", callsign="EVAC01", origin_country="United States",
        lat=35.3340, lon=139.3890, altitude_m=7200.0, velocity_mps=195.0,
        heading_deg=220.0, vertical_rate_mps=0.0, on_ground=False, military=True,
        operator="US Navy / JMSDF Liaison", aircraft_class="transport",
    ),
    FlightRecord(
        icao24="a012bc", callsign="VIPER11", origin_country="United States",
        lat=49.4369, lon=7.6003, altitude_m=4500.0, velocity_mps=280.0,
        heading_deg=310.0, vertical_rate_mps=15.0, on_ground=False, military=True,
        operator="USAF 52nd Fighter Wing", aircraft_class="fighter",
    ),
    FlightRecord(
        icao24="a38b91", callsign="DAL452", origin_country="United States",
        lat=33.6407, lon=-84.4277, altitude_m=11200.0, velocity_mps=245.0,
        heading_deg=90.0, vertical_rate_mps=0.0, on_ground=False, military=False,
        operator="Delta Air Lines", aircraft_class="jet",
    ),
]

MOCK_VESSELS: list[VesselRecord] = [
    VesselRecord(
        mmsi="367123456", name="USNS COMFORT", ship_type="Military / Hospital",
        lat=36.9388, lon=-76.3025, speed_kts=14.2, course_deg=180.0,
        heading_deg=182.0, nav_status="Underway using engine", destination="NORFOLK",
        length_m=272.0, width_m=32.0,
    ),
    VesselRecord(
        mmsi="211987654", name="EVER GIVEN", ship_type="Cargo / Container",
        lat=30.0150, lon=32.5500, speed_kts=12.0, course_deg=345.0,
        heading_deg=345.0, nav_status="Underway using engine", destination="ROTTERDAM",
        length_m=400.0, width_m=59.0,
    ),
    VesselRecord(
        mmsi="431002233", name="JS HYUGA (DDH-181)", ship_type="Military / Destroyer",
        lat=35.2917, lon=139.6667, speed_kts=18.5, course_deg=95.0,
        heading_deg=94.0, nav_status="Underway using engine", destination="YOKOSUKA",
        length_m=197.0, width_m=33.0,
    ),
    VesselRecord(
        mmsi="538004567", name="PACIFIC VOYAGER", ship_type="Tanker / Crude",
        lat=1.2902, lon=103.8519, speed_kts=10.4, course_deg=260.0,
        heading_deg=260.0, nav_status="Underway using engine", destination="SINGAPORE",
        length_m=333.0, width_m=60.0,
    ),
]

MOCK_EARTHQUAKES: list[EarthquakeRecord] = [
    EarthquakeRecord(
        event_id="us7000m9xz", title="M 6.7 - 54 km SE of Sendai, Japan",
        magnitude=6.7, place="54 km SE of Sendai, Japan", lat=38.0123, lon=141.4567,
        depth_km=42.0, time_utc=datetime.now(timezone.utc).isoformat(),
        tsunami_alert=False, url="https://earthquake.usgs.gov/earthquakes/eventpage/us7000m9xz",
    ),
    EarthquakeRecord(
        event_id="us6000k1aa", title="M 4.8 - 12 km N of Ridgecrest, California",
        magnitude=4.8, place="12 km N of Ridgecrest, California", lat=35.7310, lon=-117.6710,
        depth_km=8.5, time_utc=(datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        tsunami_alert=False, url="https://earthquake.usgs.gov/earthquakes/eventpage/us6000k1aa",
    ),
    EarthquakeRecord(
        event_id="us5000j2bb", title="M 7.2 - Vanuatu Region",
        magnitude=7.2, place="Vanuatu Region", lat=-15.3400, lon=167.2100,
        depth_km=135.0, time_utc=(datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
        tsunami_alert=True, url="https://earthquake.usgs.gov/earthquakes/eventpage/us5000j2bb",
    ),
]

MOCK_FIRMS: list[ThermalHotspotRecord] = [
    ThermalHotspotRecord(
        lat=34.1808, lon=-118.3090, brightness_kelvin=365.4, frp_mw=142.5,
        confidence="high", satellite="VIIRS_NOAA20",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"), daynight="D",
    ),
    ThermalHotspotRecord(
        lat=-33.8688, lon=151.2093, brightness_kelvin=348.2, frp_mw=88.0,
        confidence="nominal", satellite="MODIS_TERRA",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"), daynight="D",
    ),
    ThermalHotspotRecord(
        lat=44.0521, lon=-121.3153, brightness_kelvin=382.1, frp_mw=215.3,
        confidence="high", satellite="VIIRS_NOAA20",
        acquisition_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"), daynight="N",
    ),
]

__all__ = [
    "EARTH_R_KM",
    "MOCK_EARTHQUAKES",
    "MOCK_FIRMS",
    "MOCK_FLIGHTS",
    "MOCK_VESSELS",
    "asyncio_wrap",
]
