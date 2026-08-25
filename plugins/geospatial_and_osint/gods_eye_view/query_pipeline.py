"""Composable Spatial Query Pipeline and RFC 7946 GeoJSON Exporter.

Executes structured multi-layer spatial filtering, compound attribute predicates,
statistical aggregations, and standard GeoJSON transformations.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from .spatial_index import haversine_km, point_in_polygon


class SpatialQueryPipeline:
    """Analytical pipeline for spatial datasets and OSINT telemetry."""

    @staticmethod
    def apply_predicate(val: Any, op: str, target: Any) -> bool:
        """Evaluate a single atomic attribute predicate."""
        if val is None:
            return False

        op_clean = op.lower().strip()
        try:
            if op_clean == "eq":
                return str(val).lower() == str(target).lower()
            if op_clean == "neq":
                return str(val).lower() != str(target).lower()
            if op_clean == "contains":
                return str(target).lower() in str(val).lower()
            if op_clean == "starts_with":
                return str(val).lower().startswith(str(target).lower())
            if op_clean == "gt":
                return float(val) > float(target)
            if op_clean == "gte":
                return float(val) >= float(target)
            if op_clean == "lt":
                return float(val) < float(target)
            if op_clean == "lte":
                return float(val) <= float(target)
            if op_clean == "in":
                if isinstance(target, (list, tuple, set)):
                    return any(str(val).lower() == str(t).lower() for t in target)
                return str(val).lower() in str(target).lower()
            if op_clean == "between":
                if isinstance(target, (list, tuple)) and len(target) == 2:
                    return float(target[0]) <= float(val) <= float(target[1])
                return False
            if op_clean == "regex":
                return bool(re.search(str(target), str(val), re.IGNORECASE))
        except (ValueError, TypeError):
            return False
        return True

    @classmethod
    def filter_records(
        cls,
        records: list[dict[str, Any]],
        filters: list[dict[str, Any]] | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: list[float] | None = None,
        polygon: list[tuple[float, float]] | None = None,
    ) -> list[dict[str, Any]]:
        """Filter records by spatial boundaries and attribute predicates."""
        result: list[dict[str, Any]] = []

        for r in records:
            r_lat = r.get("lat")
            r_lon = r.get("lon")

            # 1. Spatial Radius Check
            if lat is not None and lon is not None and radius_km is not None:
                if r_lat is None or r_lon is None:
                    continue
                d = haversine_km(lat, lon, float(r_lat), float(r_lon))
                if d > radius_km:
                    continue
                r["_distance_km"] = round(d, 2)

            # 2. Bounding Box Check
            if bbox and len(bbox) == 4:
                if r_lat is None or r_lon is None:
                    continue
                n, s, w, e = bbox
                if not (s <= float(r_lat) <= n and w <= float(r_lon) <= e):
                    continue

            # 3. Polygon Check
            if polygon and len(polygon) >= 3:
                if r_lat is None or r_lon is None:
                    continue
                if not point_in_polygon(float(r_lat), float(r_lon), polygon):
                    continue

            # 4. Attribute Predicates
            if filters:
                match = True
                for f in filters:
                    field = f.get("field")
                    op = f.get("op", "eq")
                    val = f.get("value")
                    if field and val is not None:
                        if not cls.apply_predicate(r.get(field), op, val):
                            match = False
                            break
                if not match:
                    continue

            result.append(r)

        return result

    @staticmethod
    def compute_aggregations(records: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute summary metrics and statistical distributions."""
        aggs: dict[str, Any] = {"count": len(records)}
        numeric_fields = [
            "altitude_m",
            "velocity_mps",
            "speed_kts",
            "magnitude",
            "depth_km",
            "frp_mw",
            "brightness_kelvin",
            "_distance_km",
        ]

        for nf in numeric_fields:
            vals = [float(r[nf]) for r in records if r.get(nf) is not None]
            if vals:
                aggs[f"avg_{nf}"] = round(sum(vals) / len(vals), 2)
                aggs[f"min_{nf}"] = min(vals)
                aggs[f"max_{nf}"] = max(vals)
                aggs[f"sum_{nf}"] = round(sum(vals), 2)

        # Categorical grouping summaries
        for cat in ["origin_country", "ship_type", "satellite", "military", "aircraft_class", "infra_type"]:
            cat_vals = [str(r[cat]) for r in records if r.get(cat) is not None]
            if cat_vals:
                counts: dict[str, int] = {}
                for cv in cat_vals:
                    counts[cv] = counts.get(cv, 0) + 1
                # Top 5 most frequent categories
                top_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                aggs[f"top_{cat}"] = dict(top_cats)

        return aggs

    @staticmethod
    def to_geojson(records: list[dict[str, Any]], layer_name: str = "geospatial_layer") -> dict[str, Any]:
        """Convert record dictionaries into an RFC 7946 GeoJSON FeatureCollection."""
        features: list[dict[str, Any]] = []

        for r in records:
            lat = r.get("lat")
            lon = r.get("lon")
            if lat is None or lon is None:
                continue

            # Clone properties omitting raw coordinates from inner dict
            props = {k: v for k, v in r.items() if k not in ("lat", "lon")}
            props["layer"] = layer_name

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "properties": props,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "name": layer_name,
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }


class QuerySessionStore:
    """Manages ephemeral conversational query session memory."""

    def __init__(self, max_sessions: int = 100, session_ttl_sec: float = 1800.0) -> None:
        self._sessions: dict[str, tuple[float, list[dict[str, Any]]]] = {}
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl_sec

    def save_session(self, records: list[dict[str, Any]]) -> str:
        """Store query result set and return unique session token."""
        self._prune_expired()
        token = f"sess_{uuid.uuid4().hex[:12]}"
        self._sessions[token] = (time.time(), list(records))
        if len(self._sessions) > self.max_sessions:
            oldest_key = min(self._sessions.keys(), key=lambda k: self._sessions[k][0])
            del self._sessions[oldest_key]
        return token

    def get_session(self, token: str) -> list[dict[str, Any]] | None:
        """Retrieve result set for a session token if not expired."""
        entry = self._sessions.get(token)
        if entry is None:
            return None
        created_at, records = entry
        if time.time() - created_at > self.session_ttl:
            del self._sessions[token]
            return None
        return list(records)

    def _prune_expired(self) -> None:
        """Remove sessions past TTL."""
        now = time.time()
        expired = [k for k, (t, _) in self._sessions.items() if now - t > self.session_ttl]
        for k in expired:
            del self._sessions[k]
