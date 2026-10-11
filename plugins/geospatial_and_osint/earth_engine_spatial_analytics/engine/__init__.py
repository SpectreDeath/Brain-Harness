"""Earth Engine Spatial Analytics modular engine subpackage facade."""

from __future__ import annotations

from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.catalog import (
    CATALOG_DATASETS,
    query_data_catalog,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.core import (
    EarthEngineSpatialAnalyticsEngine,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.models import (
    EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
    CatalogDataset,
    EarthEngineSpatialAnalyticsService,
    ZonalStatsRequest,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.resolvers import (
    get_default_spatial_engine,
    resolve_earth_engine_spatial_analytics,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.tasks import (
    manage_tasks,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.terrain import (
    compute_terrain_metrics,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.vector import (
    execute_vector_query,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.zonal import (
    compute_zonal_statistics,
)

__all__ = [
    "CATALOG_DATASETS",
    "EARTH_ENGINE_SPATIAL_ANALYTICS_KEY",
    "CatalogDataset",
    "EarthEngineSpatialAnalyticsEngine",
    "EarthEngineSpatialAnalyticsService",
    "ZonalStatsRequest",
    "compute_terrain_metrics",
    "compute_zonal_statistics",
    "execute_vector_query",
    "get_default_spatial_engine",
    "manage_tasks",
    "query_data_catalog",
    "resolve_earth_engine_spatial_analytics",
]
