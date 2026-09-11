# Google Earth Engine Spatial Analytics Plugin

`plugin.earth_engine_spatial_analytics` provides vector geometry operations, zonal reducers (mean, sum, min, max, stdDev), digital elevation model (DEM) terrain modeling, public dataset discovery, and asynchronous batch task management.

## Architecture

- **Domain Category**: `plugins/geospatial_and_osint/` (Rule 18)
- **Isolation Mode**: `SUBPROCESS` (Rule 5 & Rule 7)
- **Service Key**: `service.earth_engine_spatial_analytics` (`EarthEngineSpatialAnalyticsService`)
- **Dependencies**: Requires `service.earth_engine_imagery` (Rule 3)

## Available Tools

1. `ee_zonal_statistics`: Compute spatial reductions over raster bands within vector polygon regions.
2. `ee_analyze_terrain`: Calculate elevation, slope, aspect, and hillshade relief from digital elevation models.
3. `ee_vector_spatial_query`: Query and filter FeatureCollections with attribute predicates and spatial bounding geometries.
4. `ee_query_data_catalog`: Discover and search public Earth Engine Data Catalog datasets by topic and environmental theme.
5. `ee_manage_batch_task`: Inspect status, list, monitor, or cancel background export/import batch jobs.
