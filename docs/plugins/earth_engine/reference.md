# Reference: Earth Engine Plugin API & Service Specification

Technical specification of service interfaces, typed service keys, and tool parameters for `plugin.earth_engine_imagery` and `plugin.earth_engine_spatial_analytics`.

---

## 1. Service Keys & IoC Contracts

| Service Key Constant | String Identifier | Protocol | Providing Plugin | Required By |
| :--- | :--- | :--- | :--- | :--- |
| `EARTH_ENGINE_IMAGERY_KEY` | `service.earth_engine_imagery` | `EarthEngineImageryService` | `plugin.earth_engine_imagery` | `plugin.earth_engine_spatial_analytics` |
| `EARTH_ENGINE_SPATIAL_ANALYTICS_KEY` | `service.earth_engine_spatial_analytics` | `EarthEngineSpatialAnalyticsService` | `plugin.earth_engine_spatial_analytics` | Swarm Agents & Pipelines |

---

## 2. Tools: `plugin.earth_engine_imagery`

### `ee_search_image_collection`
- **Description**: Filter satellite image collections by bounding box, date range, and cloud coverage.
- **Parameters**:
  - `collection_id` (`string`, required): Earth Engine collection asset path (e.g. `'COPERNICUS/S2_SR_HARMONIZED'`).
  - `bbox` (`list[float]`, optional): Bounding box `[min_lon, min_lat, max_lon, max_lat]` in EPSG:4326.
  - `start_date` (`string`, optional): Start date `'YYYY-MM-DD'`. Default `'2026-01-01'`.
  - `end_date` (`string`, optional): End date `'YYYY-MM-DD'`. Default `'2026-06-01'`.
  - `max_cloud_cover` (`float`, optional): Maximum cloud cover percentage `(0.0 - 100.0)`. Default `20.0`.
  - `limit` (`int`, optional): Scene count cap. Default `10`.
- **Returns**: `dict[str, Any]` with fields `status`, `mode`, `collection_id`, `total_found`, `scenes`.

### `ee_compute_spectral_index`
- **Description**: Compute multi-spectral vegetation, water, or burn severity indices.
- **Parameters**:
  - `image_id` (`string`, required): Target image asset ID.
  - `index_type` (`string`, optional): `'NDVI'`, `'NDWI'`, `'EVI'`, `'NBR'`, or `'CUSTOM'`. Default `'NDVI'`.
  - `nir_band` (`string`, optional): Near-infrared band. Default `'B8'`.
  - `red_band` (`string`, optional): Red band. Default `'B4'`.
  - `blue_band` (`string`, optional): Blue band. Default `'B2'`.
  - `swir_band` (`string`, optional): Short-wave infrared band. Default `'B11'`.
  - `custom_formula` (`string`, optional): Mathematical expression when `index_type` is `'CUSTOM'`.
- **Returns**: `dict[str, Any]` with fields `status`, `mode`, `image_id`, `index_type`, `formula`, `output_band`.

### `ee_composite_timeseries`
- **Description**: Compute temporal composite reduction across an image collection with QA masking.
- **Parameters**:
  - `collection_id` (`string`, required): Collection asset path.
  - `bbox` (`list[float]`, optional): Analysis bounding box.
  - `start_date` (`string`, optional): Temporal window start.
  - `end_date` (`string`, optional): Temporal window end.
  - `composite_method` (`string`, optional): `'median'`, `'mean'`, `'min'`, `'max'`, `'greenest_pixel'`. Default `'median'`.
  - `mask_clouds` (`bool`, optional): Whether to apply cloud masking. Default `True`.
- **Returns**: `dict[str, Any]` with fields `status`, `mode`, `collection_id`, `composite_method`, `mask_clouds_applied`.

### `ee_get_image_thumbnail_url`
- **Description**: Generate visual preview thumbnail URL and tile metadata.
- **Parameters**:
  - `image_id` (`string`, required): Target image asset ID.
  - `bands` (`list[str]`, optional): Bands for visualization (e.g. `['B4', 'B3', 'B2']`).
  - `min_val` (`float`, optional): Minimum display stretch value. Default `0.0`.
  - `max_val` (`float`, optional): Maximum display stretch value. Default `3000.0`.
  - `dimensions` (`int`, optional): Pixel size of square thumbnail. Default `512`.
  - `palette` (`list[str]`, optional): Hex color palette list.
- **Returns**: `dict[str, Any]` with fields `status`, `thumbnail_url`, `vis_params`.

### `ee_describe_image`
- **Description**: Retrieve image metadata, band definitions, resolution, and CRS.
- **Parameters**:
  - `image_id` (`string`, required): Target image asset ID.
- **Returns**: `dict[str, Any]` with fields `status`, `bands`, `spatial_resolution_meters`, `crs`, `sensor`.

---

## 3. Tools: `plugin.earth_engine_spatial_analytics`

### `ee_zonal_statistics`
- **Description**: Compute spatial reduction statistics over raster bands within vector polygon regions.
- **Parameters**:
  - `image_id` (`string`, required): Target raster asset ID.
  - `geometry_geojson` (`dict`, required): GeoJSON Polygon/MultiPolygon boundary.
  - `reducer` (`string`, optional): `'mean'`, `'sum'`, `'min'`, `'max'`, `'stddev'`, `'median'`, `'count'`. Default `'mean'`.
  - `scale_meters` (`float`, optional): Nominal evaluation pixel scale. Default `30.0`.
  - `bands` (`list[str]`, optional): Band subset to reduce.
- **Returns**: `dict[str, Any]` with fields `status`, `reducer`, `scale_meters`, `statistics`.

### `ee_analyze_terrain`
- **Description**: Extract terrain metrics (elevation, slope, aspect, hillshade) from DEMs.
- **Parameters**:
  - `dem_asset` (`string`, optional): DEM asset ID. Default `'USGS/3DEP/10m'`.
  - `bbox` (`list[float]`, optional): Region bounding box.
  - `compute_slope` (`bool`, optional): Compute slope degrees. Default `True`.
  - `compute_aspect` (`bool`, optional): Compute aspect degrees. Default `True`.
  - `compute_hillshade` (`bool`, optional): Compute shaded relief. Default `True`.
- **Returns**: `dict[str, Any]` with fields `status`, `dem_asset`, `terrain_metrics`.

### `ee_vector_spatial_query`
- **Description**: Query and filter vector FeatureCollections by attributes and geometry.
- **Parameters**:
  - `table_asset` (`string`, required): Vector table asset ID.
  - `filter_property` (`string`, optional): Attribute property name.
  - `filter_value` (`string`, optional): Attribute value string.
  - `geometry_filter` (`dict`, optional): GeoJSON polygon boundary.
  - `limit` (`int`, optional): Feature limit cap. Default `25`.
- **Returns**: `dict[str, Any]` with fields `status`, `table_asset`, `features_count`, `features`.

### `ee_query_data_catalog`
- **Description**: Search public Earth Engine Data Catalog datasets by keyword/tag.
- **Parameters**:
  - `query` (`string`, optional): Search keyword.
  - `category` (`string`, optional): Theme filter (`'climate'`, `'weather'`, `'imagery'`, `'elevation'`, `'landcover'`, `'oceans'`).
  - `tags` (`list[str]`, optional): Keyword tags list.
  - `limit` (`int`, optional): Maximum results. Default `10`.
- **Returns**: `dict[str, Any]` with fields `status`, `total_found`, `datasets`.

### `ee_manage_batch_task`
- **Description**: Monitor, list, or cancel background asynchronous export/import batch jobs.
- **Parameters**:
  - `action` (`string`, optional): `'list'`, `'status'`, `'cancel'`. Default `'list'`.
  - `task_id` (`string`, optional): Target task ID.
  - `limit` (`int`, optional): List cap. Default `10`.
- **Returns**: `dict[str, Any]` with fields `status`, `action`, `tasks` or `task_id`.
