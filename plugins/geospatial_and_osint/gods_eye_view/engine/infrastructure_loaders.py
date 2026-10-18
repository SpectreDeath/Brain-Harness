"""Dataset loader helpers for offline critical infrastructure GeoJSON/GeoJSONL feeds."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..infrastructure_store import InfrastructureStore
    from ..models import InfrastructureRecord


def load_external_datasets(store: InfrastructureStore, data_dir: str) -> None:
    """Load external GeoJSON and GeoJSONL datasets into the infrastructure store."""
    from ..models import InfrastructureRecord

    if not os.path.exists(data_dir):
        return

    # 1. Ingest Submarine Cables Landing Points GeoJSON
    landing_path = os.path.join(data_dir, "telegeography_submarine_cables", "landing-point-geo.json")
    if os.path.exists(landing_path):
        try:
            with open(landing_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for feat in data.get("features", [])[:500]:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    if coords and len(coords) >= 2:
                        rec = InfrastructureRecord(
                            infra_type="landing_point",
                            name=props.get("name", "Landing Point"),
                            lon=float(coords[0]),
                            lat=float(coords[1]),
                            properties=props,
                            country=props.get("country"),
                        )
                        store.add_record(rec)
        except Exception:
            pass

    # 2. Ingest Submarine Cables GeoJSON
    cables_path = os.path.join(data_dir, "telegeography_submarine_cables", "cable-geo.json")
    if os.path.exists(cables_path):
        try:
            with open(cables_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for feat in data.get("features", [])[:500]:
                    props = feat.get("properties", {})
                    coords = props.get("coordinates")
                    if not coords:
                        geom = feat.get("geometry", {})
                        gcoords = geom.get("coordinates", [])
                        if gcoords and isinstance(gcoords[0], list):
                            coords = gcoords[0]
                    if coords and len(coords) >= 2:
                        rec = InfrastructureRecord(
                            infra_type="submarine_cable",
                            name=props.get("name", "Submarine Cable"),
                            lon=float(coords[0]),
                            lat=float(coords[1]),
                            properties=props,
                            country=props.get("country"),
                        )
                        store.add_record(rec)
        except Exception:
            pass

    # 3. Ingest Datacenters GeoJSONL
    dc_path = os.path.join(data_dir, "datacenters", "datacenters.geojsonl")
    if os.path.exists(dc_path):
        try:
            with open(dc_path, "r", encoding="utf-8") as f:
                count = 0
                for line in f:
                    if not line.strip():
                        continue
                    feat = json.loads(line)
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    if coords and len(coords) >= 2:
                        name = props.get("name")
                        if not name and isinstance(props.get("tags"), dict):
                            name = props["tags"].get("name") or props["tags"].get("operator")
                        rec = InfrastructureRecord(
                            infra_type="datacenter",
                            name=name or props.get("operator") or "Hyperscale Datacenter",
                            lon=float(coords[0]),
                            lat=float(coords[1]),
                            properties=props,
                            country=props.get("country"),
                        )
                        store.add_record(rec)
                        count += 1
                        if count >= 500:
                            break
        except Exception:
            pass

    # 4. Ingest Dams GeoJSONL
    dams_path = os.path.join(data_dir, "dams", "dams.geojsonl")
    if os.path.exists(dams_path):
        try:
            with open(dams_path, "r", encoding="utf-8") as f:
                count = 0
                for line in f:
                    if not line.strip():
                        continue
                    feat = json.loads(line)
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    if coords and len(coords) >= 2:
                        rec = InfrastructureRecord(
                            infra_type="dam",
                            name=props.get("name") or "Major Dam",
                            lon=float(coords[0]),
                            lat=float(coords[1]),
                            properties=props,
                            country=props.get("country"),
                        )
                        store.add_record(rec)
                        count += 1
                        if count >= 500:
                            break
        except Exception:
            pass

    # 5. Ingest High-Priority Military Installations from OSM
    mil_path = os.path.join(data_dir, "osm_military_names", "names.json")
    if os.path.exists(mil_path):
        try:
            with open(mil_path, "r", encoding="utf-8") as f:
                mil_data = json.load(f)
                records = mil_data.get("records", [])
                classes = mil_data.get("classes", [])
                count = 0
                for row in records:
                    if len(row) >= 9:
                        name = row[1]
                        lon = float(row[2])
                        lat = float(row[3])
                        class_idx = row[8]
                        class_name = classes[class_idx] if 0 <= class_idx < len(classes) else "installation"
                        if class_name in ("airfield", "naval_base", "base"):
                            rec = InfrastructureRecord(
                                infra_type="installation",
                                name=name,
                                lon=lon,
                                lat=lat,
                                properties={"classification": class_name, "osm_ref": row[0]},
                                country=None,
                            )
                            store.add_record(rec)
                            count += 1
                            if count >= 500:
                                break
        except Exception:
            pass
