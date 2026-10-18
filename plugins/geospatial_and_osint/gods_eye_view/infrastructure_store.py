"""Offline Critical Infrastructure asset store and spatial indexing engine.

Supports submarine fiber optic cables, landing stations, hyperscale datacenters,
dams, reservoirs, and curated defense installations indexed via SpatialHashGrid.
"""

from __future__ import annotations

import os
from typing import Any

from .builtin_infrastructure import BUILTIN_INFRASTRUCTURE
from .engine.infrastructure_loaders import load_external_datasets
from .models import InfrastructureRecord
from .spatial_index import SpatialHashGrid, haversine_km

__all__ = ["BUILTIN_INFRASTRUCTURE", "InfrastructureStore", "haversine_km"]


class InfrastructureStore:
    """Indexed catalog of global infrastructure assets backed by SpatialHashGrid."""

    def __init__(self, external_data_dir: str | None = None) -> None:
        self.records: list[InfrastructureRecord] = []
        self.grid: SpatialHashGrid[InfrastructureRecord] = SpatialHashGrid(
            cell_size_deg=1.0,
            lat_extractor=lambda r: r.lat,
            lon_extractor=lambda r: r.lon,
        )
        self.external_data_dir = (
            external_data_dir
            or os.environ.get("GEV_DATA_DIR")
            or r"D:\GitHub\cloned\gods-eye-view\src\data\local_data"
        )
        self._load_all_records()

    def _load_all_records(self) -> None:
        """Load built-in and external dataset files and populate spatial grid."""
        for rec in BUILTIN_INFRASTRUCTURE:
            self.add_record(rec)

        load_external_datasets(self, self.external_data_dir)

    def add_record(self, rec: InfrastructureRecord) -> None:
        """Add record and index in spatial hash grid."""
        self.records.append(rec)
        if rec.lat is not None and rec.lon is not None:
            self.grid.insert(rec, rec.lat, rec.lon)

    _add_record = add_record

    def query(
        self,
        infra_type: str | None = None,
        search_query: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        limit: int = 100,
    ) -> list[InfrastructureRecord]:
        """Query infrastructure assets using spatial grid pruning and text filtering."""
        type_norm = infra_type.lower().strip() if infra_type and infra_type != "all" else None
        q_lower = search_query.lower().strip() if search_query else None

        # 1. Fast path: Spatial grid index query
        if lat is not None and lon is not None and radius_km is not None:
            spatial_candidates = self.grid.query_radius(lat, lon, radius_km)
            candidates: list[tuple[float | None, InfrastructureRecord]] = [
                (dist, item) for dist, item in spatial_candidates
            ]
        else:
            candidates = [(None, r) for r in self.records]

        results: list[tuple[float | None, InfrastructureRecord]] = []
        for dist, rec in candidates:
            if type_norm and rec.infra_type != type_norm:
                continue

            if q_lower:
                text_match = (
                    q_lower in rec.name.lower()
                    or (rec.country and q_lower in rec.country.lower())
                    or any(q_lower in str(v).lower() for v in rec.properties.values())
                )
                if not text_match:
                    continue

            results.append((dist, rec))

        if lat is not None and lon is not None and radius_km is None:
            results = [
                (haversine_km(lat, lon, r.lat, r.lon) if r.lat is not None and r.lon is not None else None, r)
                for _, r in results
            ]
            results.sort(key=lambda x: (x[0] is None, x[0] or 0.0))

        return [rec for _, rec in results[:limit]]
