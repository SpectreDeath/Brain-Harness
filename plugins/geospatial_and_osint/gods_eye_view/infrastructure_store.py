"""Offline Critical Infrastructure asset store and spatial indexing engine.

Supports submarine fiber optic cables, landing stations, hyperscale datacenters,
dams, reservoirs, and curated defense installations.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

from .models import InfrastructureRecord

EARTH_R_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great-Circle distance between two coordinates in kilometers."""
    d2r = math.pi / 180.0
    d_lat = (lat2 - lat1) * d2r
    d_lon = (lon2 - lon1) * d2r
    a = math.sin(d_lat / 2.0) ** 2 + math.cos(lat1 * d2r) * math.cos(lat2 * d2r) * math.sin(d_lon / 2.0) ** 2
    c = 2.0 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_R_KM * c


# Curated high-priority global critical infrastructure fallback registry
BUILTIN_INFRASTRUCTURE: list[InfrastructureRecord] = [
    InfrastructureRecord(
        infra_type="submarine_cable",
        name="MAREA Transatlantic Cable",
        lat=36.8529,
        lon=-75.9780,
        properties={"length_km": 6605, "capacity_tbps": 224, "owners": ["Microsoft", "Meta", "Telxius"], "rfs": 2018},
        country="USA - Spain",
    ),
    InfrastructureRecord(
        infra_type="submarine_cable",
        name="Dunant Cable",
        lat=40.7128,
        lon=-74.0060,
        properties={"length_km": 6400, "capacity_tbps": 250, "owners": ["Google"], "rfs": 2020},
        country="USA - France",
    ),
    InfrastructureRecord(
        infra_type="submarine_cable",
        name="Grace Hopper Cable",
        lat=50.7967,
        lon=-1.1090,
        properties={"length_km": 6250, "capacity_tbps": 340, "owners": ["Google"], "rfs": 2022},
        country="USA - UK - Spain",
    ),
    InfrastructureRecord(
        infra_type="submarine_cable",
        name="Pacific Light Cable Network (PLCN)",
        lat=33.7490,
        lon=-118.2860,
        properties={"length_km": 12800, "capacity_tbps": 144, "owners": ["Google", "Meta"], "rfs": 2020},
        country="USA - Taiwan - Philippines",
    ),
    InfrastructureRecord(
        infra_type="landing_point",
        name="Virginia Beach Cable Landing Station",
        lat=36.8529,
        lon=-75.9780,
        properties={"landing_cables": ["MAREA", "BRUSA", "Dunant", "SAEx1"]},
        country="United States",
    ),
    InfrastructureRecord(
        infra_type="landing_point",
        name="Bude Subsea Cable Station",
        lat=50.8305,
        lon=-4.5437,
        properties={"landing_cables": ["Apollo", "Yellow", "Grace Hopper", "TAT-14"]},
        country="United Kingdom",
    ),
    InfrastructureRecord(
        infra_type="landing_point",
        name="Marseille Interxion Landing Station",
        lat=43.2965,
        lon=5.3698,
        properties={"landing_cables": ["SEA-ME-WE 4", "SEA-ME-WE 5", "PEACE", "2Africa", "AAE-1"]},
        country="France",
    ),
    InfrastructureRecord(
        infra_type="datacenter",
        name="Equinix Ashburn DC (Data Center Alley)",
        lat=39.0438,
        lon=-77.4874,
        properties={"campus": "Ashburn VA", "sqft": 1200000, "power_mw": 350, "tier": "Tier IV"},
        country="United States",
    ),
    InfrastructureRecord(
        infra_type="datacenter",
        name="Google The Dalles Hyperscale Center",
        lat=45.5946,
        lon=-121.1786,
        properties={"power_source": "Hydroelectric", "cooling": "Columbia River", "status": "Operational"},
        country="United States",
    ),
    InfrastructureRecord(
        infra_type="datacenter",
        name="Microsoft Quincy Hyperscale Center",
        lat=47.2343,
        lon=-119.8526,
        properties={"power_source": "Columbia Basin Hydro", "power_mw": 200},
        country="United States",
    ),
    InfrastructureRecord(
        infra_type="dam",
        name="Three Gorges Dam",
        lat=30.8239,
        lon=111.0033,
        properties={"capacity_mw": 22500, "river": "Yangtze", "height_m": 181, "reservoir_capacity_km3": 39.3},
        country="China",
    ),
    InfrastructureRecord(
        infra_type="dam",
        name="Hoover Dam",
        lat=36.0156,
        lon=-114.7378,
        properties={"capacity_mw": 2080, "river": "Colorado", "height_m": 221.4, "lake": "Lake Mead"},
        country="United States",
    ),
    InfrastructureRecord(
        infra_type="dam",
        name="Itaipu Dam",
        lat=-25.4091,
        lon=-54.5889,
        properties={"capacity_mw": 14000, "river": "Parana", "height_m": 196},
        country="Brazil - Paraguay",
    ),
    InfrastructureRecord(
        infra_type="installation",
        name="Ramstein Air Base (USAF)",
        lat=49.4369,
        lon=7.6003,
        properties={"branch": "United States Air Force", "role": "Headquarters USAFE-AFAFRICA", "runway_m": 3200},
        country="Germany",
    ),
    InfrastructureRecord(
        infra_type="installation",
        name="Kadena Air Base (USAF)",
        lat=26.3556,
        lon=127.7675,
        properties={"branch": "United States Air Force", "role": "18th Wing Hub Asia-Pacific", "runway_m": 3688},
        country="Japan",
    ),
    InfrastructureRecord(
        infra_type="installation",
        name="Yokosuka Naval Base",
        lat=35.2917,
        lon=139.6667,
        properties={"branch": "United States Navy / JMSDF", "role": "Commander Fleet Activities Yokosuka (Carrier Strike Group)"},
        country="Japan",
    ),
    InfrastructureRecord(
        infra_type="installation",
        name="Naval Station Norfolk",
        lat=36.9388,
        lon=-76.3025,
        properties={"branch": "United States Navy", "role": "Largest Naval Base in the World", "piers": 14},
        country="United States",
    ),
]


class InfrastructureStore:
    """Indexed catalog of global infrastructure assets."""

    def __init__(self, external_data_dir: str | None = None) -> None:
        self.records: list[InfrastructureRecord] = list(BUILTIN_INFRASTRUCTURE)
        self.external_data_dir = external_data_dir or r"D:\GitHub\cloned\gods-eye-view-main\gods-eye-view-main\src\data\local_data"
        self._load_local_data_sources()

    def _load_local_data_sources(self) -> None:
        """Scan and ingest local GeoJSON / GeoJSONL files from the cloned repository if present."""
        if not os.path.exists(self.external_data_dir):
            return

        # 1. Ingest Submarine Cables Landing Points GeoJSON
        landing_path = os.path.join(self.external_data_dir, "telegeography_submarine_cables", "landing-point-geo.json")
        if os.path.exists(landing_path):
            try:
                with open(landing_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feat in data.get("features", [])[:200]:
                        props = feat.get("properties", {})
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        if coords and len(coords) >= 2:
                            self.records.append(
                                InfrastructureRecord(
                                    infra_type="landing_point",
                                    name=props.get("name", "Landing Point"),
                                    lon=float(coords[0]),
                                    lat=float(coords[1]),
                                    properties=props,
                                    country=props.get("country"),
                                )
                            )
            except Exception:
                pass

        # 2. Ingest Datacenters GeoJSONL
        dc_path = os.path.join(self.external_data_dir, "datacenters", "datacenters.geojsonl")
        if os.path.exists(dc_path):
            try:
                with open(dc_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        feat = json.loads(line)
                        props = feat.get("properties", {})
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        if coords and len(coords) >= 2:
                            self.records.append(
                                InfrastructureRecord(
                                    infra_type="datacenter",
                                    name=props.get("name") or props.get("operator") or "Hyperscale Datacenter",
                                    lon=float(coords[0]),
                                    lat=float(coords[1]),
                                    properties=props,
                                    country=props.get("country"),
                                )
                            )
            except Exception:
                pass

        # 3. Ingest Dams GeoJSONL
        dams_path = os.path.join(self.external_data_dir, "dams", "dams.geojsonl")
        if os.path.exists(dams_path):
            try:
                with open(dams_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        feat = json.loads(line)
                        props = feat.get("properties", {})
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        if coords and len(coords) >= 2:
                            self.records.append(
                                InfrastructureRecord(
                                    infra_type="dam",
                                    name=props.get("name") or "Major Dam",
                                    lon=float(coords[0]),
                                    lat=float(coords[1]),
                                    properties=props,
                                    country=props.get("country"),
                                )
                            )
            except Exception:
                pass

    def query(
        self,
        infra_type: str | None = None,
        search_query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[InfrastructureRecord]:
        """Filter infrastructure assets by type, keyword search, or spatial proximity."""
        results: list[tuple[float | None, InfrastructureRecord]] = []

        q_lower = search_query.lower().strip() if search_query else None
        type_norm = infra_type.lower().strip() if infra_type and infra_type != "all" else None

        for rec in self.records:
            # Filter by infra_type
            if type_norm and rec.infra_type != type_norm:
                continue

            # Filter by text search
            if q_lower:
                text_match = (
                    q_lower in rec.name.lower()
                    or (rec.country and q_lower in rec.country.lower())
                    or any(q_lower in str(v).lower() for v in rec.properties.values())
                )
                if not text_match:
                    continue

            # Spatial filter
            dist: float | None = None
            if lat is not None and lon is not None and rec.lat is not None and rec.lon is not None:
                dist = haversine_km(lat, lon, rec.lat, rec.lon)
                if radius_km is not None and dist > radius_km:
                    continue

            results.append((dist, rec))

        # Sort by distance if spatial query provided, else keep initial order
        if lat is not None and lon is not None:
            results.sort(key=lambda x: (x[0] is None, x[0] or 0.0))

        return [rec for _, rec in results[:limit]]
