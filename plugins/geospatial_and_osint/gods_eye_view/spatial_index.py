"""2D Spatial Hash Grid Index for high-performance geospatial queries.

Partitions geographical coordinates into degree-based spatial buckets, accelerating
proximity, radius, k-nearest neighbors (k-NN), and bounding box queries from O(N)
to O(1) candidate lookups.
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")

EARTH_R_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great-Circle distance between two coordinates in kilometers."""
    d2r = math.pi / 180.0
    d_lat = (lat2 - lat1) * d2r
    d_lon = (lon2 - lon1) * d2r
    a = math.sin(d_lat / 2.0) ** 2 + math.cos(lat1 * d2r) * math.cos(lat2 * d2r) * math.sin(d_lon / 2.0) ** 2
    c = 2.0 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_R_KM * c


def point_in_polygon(lat: float, lon: float, vertices: list[tuple[float, float]]) -> bool:
    """Ray casting algorithm for testing if a point (lat, lon) is inside a polygon."""
    n = len(vertices)
    if n < 3:
        return False
    inside = False
    p1_lat, p1_lon = vertices[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = vertices[i % n]
        if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
            if lon <= max(p1_lon, p2_lon):
                if p1_lat != p2_lat:
                    x_inters = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                    if p1_lon == p2_lon or lon <= x_inters:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
    return inside


class SpatialHashGrid(Generic[T]):
    """2D spatial grid partitioning coordinates into degree buckets."""

    def __init__(
        self,
        cell_size_deg: float = 1.0,
        lat_extractor: Callable[[T], float | None] | None = None,
        lon_extractor: Callable[[T], float | None] | None = None,
    ) -> None:
        self.cell_size = max(0.01, cell_size_deg)
        self.lat_fn = lat_extractor or (lambda x: getattr(x, "lat", None))
        self.lon_fn = lon_extractor or (lambda x: getattr(x, "lon", None))
        self._grid: dict[tuple[int, int], list[tuple[str, float, float, T]]] = defaultdict(list)
        self._key_to_cell: dict[str, tuple[int, int]] = {}

    def _cell_coords(self, lat: float, lon: float) -> tuple[int, int]:
        """Map latitude and longitude to grid cell indices."""
        x = int(math.floor(lon / self.cell_size))
        y = int(math.floor(lat / self.cell_size))
        return (y, x)

    def insert(self, item: T, lat: float | None = None, lon: float | None = None, key: str | None = None) -> None:
        """Insert or update an entity in the spatial index."""
        i_lat = lat if lat is not None else self.lat_fn(item)
        i_lon = lon if lon is not None else self.lon_fn(item)
        if i_lat is None or i_lon is None:
            return

        i_key = key or str(id(item))
        if i_key in self._key_to_cell:
            self.remove(i_key)

        cell = self._cell_coords(i_lat, i_lon)
        self._grid[cell].append((i_key, i_lat, i_lon, item))
        self._key_to_cell[i_key] = cell

    def bulk_insert(self, items: list[T], key_fn: Callable[[T], str] | None = None) -> None:
        """Insert multiple items into the spatial grid."""
        for item in items:
            k = key_fn(item) if key_fn else None
            self.insert(item, key=k)

    def remove(self, key: str) -> bool:
        """Remove an entity by key."""
        cell = self._key_to_cell.pop(key, None)
        if cell is None:
            return False
        bucket = self._grid.get(cell, [])
        self._grid[cell] = [entry for entry in bucket if entry[0] != key]
        if not self._grid[cell]:
            self._grid.pop(cell, None)
        return True

    def clear(self) -> None:
        """Clear all entries in the spatial grid."""
        self._grid.clear()
        self._key_to_cell.clear()

    def __len__(self) -> int:
        return len(self._key_to_cell)

    def query_radius(self, lat: float, lon: float, radius_km: float) -> list[tuple[float, T]]:
        """Query all entities within radius_km, returning sorted list of (distance_km, item)."""
        # 1 degree latitude ~ 111.32 km
        lat_delta_deg = radius_km / 111.0
        # Longitude delta adjusted for latitude convergence
        cos_lat = max(0.01, math.cos(math.radians(lat)))
        lon_delta_deg = radius_km / (111.0 * cos_lat)

        min_lat, max_lat = lat - lat_delta_deg, lat + lat_delta_deg
        min_lon, max_lon = lon - lon_delta_deg, lon + lon_delta_deg

        min_y, min_x = self._cell_coords(min_lat, min_lon)
        max_y, max_x = self._cell_coords(max_lat, max_lon)

        results: list[tuple[float, T]] = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                bucket = self._grid.get((y, x))
                if not bucket:
                    continue
                for _, e_lat, e_lon, item in bucket:
                    d = haversine_km(lat, lon, e_lat, e_lon)
                    if d <= radius_km:
                        results.append((d, item))

        results.sort(key=lambda x: x[0])
        return results

    def query_bbox(self, north: float, south: float, west: float, east: float) -> list[T]:
        """Query all entities within bounding box [north, south, west, east]."""
        min_y, min_x = self._cell_coords(south, west)
        max_y, max_x = self._cell_coords(north, east)

        results: list[T] = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                bucket = self._grid.get((y, x))
                if not bucket:
                    continue
                for _, e_lat, e_lon, item in bucket:
                    if south <= e_lat <= north and west <= e_lon <= east:
                        results.append(item)
        return results

    def query_knn(self, lat: float, lon: float, k: int = 10, max_radius_km: float = 20000.0) -> list[tuple[float, T]]:
        """Find k-nearest neighbors using expanding concentric ring expansion."""
        if k <= 0 or not self._key_to_cell:
            return []

        # Start with a search radius based on grid density or minimum 50km
        current_radius = 50.0
        while current_radius <= max_radius_km:
            candidates = self.query_radius(lat, lon, current_radius)
            if len(candidates) >= k:
                return candidates[:k]
            current_radius *= 2.5

        # Fallback to query all if k not met within expanding rings
        all_candidates = self.query_radius(lat, lon, max_radius_km)
        return all_candidates[:k]

    def query_polygon(self, vertices: list[tuple[float, float]]) -> list[T]:
        """Find all entities inside an arbitrary 2D geographical polygon."""
        if len(vertices) < 3:
            return []
        lats = [v[0] for v in vertices]
        lons = [v[1] for v in vertices]
        north, south = max(lats), min(lats)
        east, west = max(lons), min(lons)

        bbox_candidates = self.query_bbox(north, south, west, east)
        results: list[T] = []
        for item in bbox_candidates:
            i_lat = self.lat_fn(item)
            i_lon = self.lon_fn(item)
            if i_lat is not None and i_lon is not None:
                if point_in_polygon(i_lat, i_lon, vertices):
                    results.append(item)
        return results
