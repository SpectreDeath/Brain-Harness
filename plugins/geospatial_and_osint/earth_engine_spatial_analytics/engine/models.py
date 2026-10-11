"""Domain models, protocols, and service keys for Earth Engine Spatial Analytics.

Enforces:
- Rule 12: Slotted & frozen dataclasses (slots=True, frozen=True)
- Rule 43: Direct attribute mutation assertion invariants
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

logger = logging.getLogger(__name__)

# Ensure Google Earth Engine source repository is accessible if cloned
_POSSIBLE_EE_PATHS = [
    Path(r"D:\GitHub\cloned\Google\earthengine-api\python"),
    Path(__file__).parent.parent / "vendor",
]
for _p in _POSSIBLE_EE_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import ee  # type: ignore
    _EE_AVAILABLE = True
except Exception as _err:
    logger.debug("earth_engine_import_offline", extra={"error": str(_err)})
    _EE_AVAILABLE = False
    ee = None  # type: ignore


@runtime_checkable
class EarthEngineSpatialAnalyticsService(Protocol):
    """Protocol for Earth Engine vector spatial analysis, zonal reducers, and catalog discovery."""

    def zonal_statistics(
        self,
        image_id: str,
        geometry_geojson: dict[str, Any],
        reducer: str = "mean",
        scale_meters: float = 30.0,
        bands: list[str] | None = None,
    ) -> dict[str, Any]:
        ...

    def analyze_terrain(
        self,
        dem_asset: str = "USGS/3DEP/10m",
        bbox: list[float] | None = None,
        compute_slope: bool = True,
        compute_aspect: bool = True,
        compute_hillshade: bool = True,
    ) -> dict[str, Any]:
        ...

    def vector_spatial_query(
        self,
        table_asset: str,
        filter_property: str = "",
        filter_value: str = "",
        geometry_filter: dict[str, Any] | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        ...

    def query_data_catalog(
        self,
        query: str = "",
        category: str = "",
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        ...

    def manage_batch_task(
        self,
        action: str = "list",
        task_id: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        ...


EARTH_ENGINE_SPATIAL_ANALYTICS_KEY: ServiceKey[EarthEngineSpatialAnalyticsService] = ServiceKey(
    "service.earth_engine_spatial_analytics"
)


@dataclass(slots=True, frozen=True)
class CatalogDataset:
    """Slotted and frozen model representing a curated Earth Engine data catalog asset."""

    dataset_id: str
    title: str
    category: str
    tags: tuple[str, ...]
    spatial_resolution_meters: float
    time_start: str
    description: str


@dataclass(slots=True, frozen=True)
class ZonalStatsRequest:
    """Slotted and frozen specification for a raster-vector zonal reduction."""

    image_id: str
    geometry_type: str
    reducer: str = "mean"
    scale_meters: float = 30.0
    bands: tuple[str, ...] = ()
