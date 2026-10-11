"""Google Earth Engine Vector Spatial Analytics, Zonal Reducers & Terrain Modeling Plugin.

Decomposed entrypoint exposing the plugin lifecycle, Click/MCP tool interfaces,
and delegating underlying domain engines to the modular engine/ subpackage.
"""

from __future__ import annotations

import logging
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from plugins.geospatial_and_osint.earth_engine_imagery.main import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryService,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine import (
    CATALOG_DATASETS,
    EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
    EarthEngineSpatialAnalyticsEngine,
    EarthEngineSpatialAnalyticsService,
    get_default_spatial_engine,
    resolve_earth_engine_spatial_analytics,
)

logger = logging.getLogger(__name__)

# Backward-compatible alias for catalog dataset index
_CATALOG_DATASETS = CATALOG_DATASETS

# Process-level default engine singleton
_SPATIAL_ENGINE = get_default_spatial_engine()


# ---------------------------------------------------------------------------
# Top-Level Entrypoint Tools
# ---------------------------------------------------------------------------


def ee_zonal_statistics(
    image_id: str,
    geometry_geojson: dict[str, Any],
    reducer: str = "mean",
    scale_meters: float = 30.0,
    bands: list[str] | None = None,
) -> dict[str, Any]:
    """Compute spatial statistics (mean, sum, min, max, stdDev) over raster bands within polygon."""
    return _SPATIAL_ENGINE.zonal_statistics(
        image_id=image_id,
        geometry_geojson=geometry_geojson,
        reducer=reducer,
        scale_meters=scale_meters,
        bands=bands,
    )


def ee_analyze_terrain(
    dem_asset: str = "USGS/3DEP/10m",
    bbox: list[float] | None = None,
    compute_slope: bool = True,
    compute_aspect: bool = True,
    compute_hillshade: bool = True,
) -> dict[str, Any]:
    """Calculate terrain metrics including elevation, slope, aspect, and hillshade."""
    return _SPATIAL_ENGINE.analyze_terrain(
        dem_asset=dem_asset,
        bbox=bbox,
        compute_slope=compute_slope,
        compute_aspect=compute_aspect,
        compute_hillshade=compute_hillshade,
    )


def ee_vector_spatial_query(
    table_asset: str,
    filter_property: str = "",
    filter_value: str = "",
    geometry_filter: dict[str, Any] | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Query and filter vector FeatureCollections (admin boundaries, watersheds, parcels)."""
    return _SPATIAL_ENGINE.vector_spatial_query(
        table_asset=table_asset,
        filter_property=filter_property,
        filter_value=filter_value,
        geometry_filter=geometry_filter,
        limit=limit,
    )


def ee_query_data_catalog(
    query: str = "",
    category: str = "",
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search and discover datasets in the public Earth Engine Data Catalog."""
    return _SPATIAL_ENGINE.query_data_catalog(
        query=query,
        category=category,
        tags=tags,
        limit=limit,
    )


def ee_manage_batch_task(
    action: str = "list",
    task_id: str = "",
    limit: int = 10,
) -> dict[str, Any]:
    """Inspect status, list, monitor, or cancel asynchronous Earth Engine export/import batch jobs."""
    return _SPATIAL_ENGINE.manage_batch_task(
        action=action,
        task_id=task_id,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Harness Plugin Implementation
# ---------------------------------------------------------------------------


class EarthEngineSpatialAnalyticsPlugin(HarnessPlugin):
    """Brain Harness plugin exposing Google Earth Engine vector spatial analytics & catalog services."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = _SPATIAL_ENGINE

    @property
    def name(self) -> str:
        return "plugin.earth_engine_spatial_analytics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google Earth Engine vector spatial analytics, zonal reducers, and catalog governance plugin."

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [EARTH_ENGINE_SPATIAL_ANALYTICS_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [EARTH_ENGINE_IMAGERY_KEY]

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(EARTH_ENGINE_SPATIAL_ANALYTICS_KEY, self._engine)
        logger.info("earth_engine_spatial_analytics_plugin_loaded")

    async def on_enable(self) -> None:
        logger.info("earth_engine_spatial_analytics_plugin_enabled")

    async def on_disable(self) -> None:
        logger.info("earth_engine_spatial_analytics_plugin_disabled")

    async def on_unload(self) -> None:
        logger.info("earth_engine_spatial_analytics_plugin_unloaded")


# Rule 45: Export module-level plugin singleton
plugin = EarthEngineSpatialAnalyticsPlugin()

__all__ = [
    "EARTH_ENGINE_SPATIAL_ANALYTICS_KEY",
    "EarthEngineImageryService",
    "EarthEngineSpatialAnalyticsEngine",
    "EarthEngineSpatialAnalyticsPlugin",
    "EarthEngineSpatialAnalyticsService",
    "ee_analyze_terrain",
    "ee_manage_batch_task",
    "ee_query_data_catalog",
    "ee_vector_spatial_query",
    "ee_zonal_statistics",
    "plugin",
    "resolve_earth_engine_spatial_analytics",
]
