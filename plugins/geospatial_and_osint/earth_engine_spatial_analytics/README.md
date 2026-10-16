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


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `ee_zonal_statistics` | `(image_id, geometry_geojson, reducer, scale_meters, bands)` | Compute spatial statistics (mean, sum, min, max, stdDev, count, histogram) over raster bands within vector polygon regions |
| `ee_analyze_terrain` | `(dem_asset, bbox, compute_slope, compute_aspect, compute_hillshade)` | Extract terrain metrics including elevation profile, slope, aspect, and hillshade from digital elevation models |
| `ee_vector_spatial_query` | `(table_asset, filter_property, filter_value, geometry_filter, limit)` | Query and filter vector FeatureCollections (administrative boundaries, watersheds, parcels) with attribute and geometry filters |
| `ee_query_data_catalog` | `(query, category, tags, limit)` | Search and discover datasets in the public Earth Engine Data Catalog by keyword, environmental theme, and tag |
| `ee_manage_batch_task` | `(action, task_id, limit)` | Inspect status, list, monitor, or cancel asynchronous Earth Engine export/import batch jobs |
