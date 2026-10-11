"""Core Earth Engine Spatial Analytics Engine coordinating sub-domain operations."""

from __future__ import annotations

import logging
from typing import Any

from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.catalog import (
    query_data_catalog as _query_catalog,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.models import (
    EarthEngineSpatialAnalyticsService,
    _EE_AVAILABLE,
    ee,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.tasks import (
    manage_tasks as _manage_tasks,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.terrain import (
    compute_terrain_metrics as _compute_terrain,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.vector import (
    execute_vector_query as _execute_vector_query,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.zonal import (
    compute_zonal_statistics as _compute_zonal_statistics,
)

logger = logging.getLogger(__name__)


class EarthEngineSpatialAnalyticsEngine(EarthEngineSpatialAnalyticsService):
    """Core analytics engine executing zonal reducers, terrain modeling, and catalog searches."""

    def __init__(self) -> None:
        self._ee_initialized = False

    def _ensure_initialized(self) -> bool:
        if not self._ee_initialized and _EE_AVAILABLE and ee is not None:
            try:
                ee.Initialize()
                self._ee_initialized = True
            except Exception as e:
                logger.debug("earth_engine_analytics_auth_offline", extra={"reason": str(e)})
                self._ee_initialized = False
        return self._ee_initialized

    def zonal_statistics(
        self,
        image_id: str,
        geometry_geojson: dict[str, Any],
        reducer: str = "mean",
        scale_meters: float = 30.0,
        bands: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compute spatial statistics (mean, sum, min, max, stdDev) over raster bands within polygon."""
        return _compute_zonal_statistics(
            image_id=image_id,
            geometry_geojson=geometry_geojson,
            reducer=reducer,
            scale_meters=scale_meters,
            bands=bands,
            ee_initialized=self._ensure_initialized(),
            ee_module=ee,
        )

    def analyze_terrain(
        self,
        dem_asset: str = "USGS/3DEP/10m",
        bbox: list[float] | None = None,
        compute_slope: bool = True,
        compute_aspect: bool = True,
        compute_hillshade: bool = True,
    ) -> dict[str, Any]:
        """Calculate terrain metrics including elevation, slope, aspect, and hillshade."""
        return _compute_terrain(
            dem_asset=dem_asset,
            bbox=bbox,
            compute_slope=compute_slope,
            compute_aspect=compute_aspect,
            compute_hillshade=compute_hillshade,
            ee_initialized=self._ensure_initialized(),
            ee_module=ee,
        )

    def vector_spatial_query(
        self,
        table_asset: str,
        filter_property: str = "",
        filter_value: str = "",
        geometry_filter: dict[str, Any] | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Query and filter vector FeatureCollections (admin boundaries, watersheds, parcels)."""
        return _execute_vector_query(
            table_asset=table_asset,
            filter_property=filter_property,
            filter_value=filter_value,
            geometry_filter=geometry_filter,
            limit=limit,
            ee_initialized=self._ensure_initialized(),
            ee_module=ee,
        )

    def query_data_catalog(
        self,
        query: str = "",
        category: str = "",
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search and discover datasets in the public Earth Engine Data Catalog."""
        return _query_catalog(
            query=query,
            category=category,
            tags=tags,
            limit=limit,
        )

    def manage_batch_task(
        self,
        action: str = "list",
        task_id: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Inspect status, list, monitor, or cancel asynchronous Earth Engine export/import batch jobs."""
        return _manage_tasks(
            action=action,
            task_id=task_id,
            limit=limit,
            ee_initialized=self._ensure_initialized(),
            ee_module=ee,
        )
