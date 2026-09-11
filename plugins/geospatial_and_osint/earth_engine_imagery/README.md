# Google Earth Engine Imagery Plugin

`plugin.earth_engine_imagery` bridges satellite image discovery, multi-spectral index calculation (NDVI, NDWI, EVI, NBR), temporal compositing, and visual thumbnail generation into Brain Harness.

## Architecture

- **Domain Category**: `plugins/geospatial_and_osint/` (Rule 18)
- **Isolation Mode**: `SUBPROCESS` (Rule 5 & Rule 7)
- **Service Key**: `service.earth_engine_imagery` (`EarthEngineImageryService`)

## Available Tools

1. `ee_search_image_collection`: Filter satellite collections (Sentinel-2, Landsat, MODIS) by bounding box, date range, and maximum cloud cover.
2. `ee_compute_spectral_index`: Compute NDVI, NDWI, EVI, NBR, or custom band expressions.
3. `ee_composite_timeseries`: Generate multi-temporal composites (median, mean, min, max, greenest pixel) with cloud masking.
4. `ee_get_image_thumbnail_url`: Generate visual preview thumbnail URLs and map tile endpoints.
5. `ee_describe_image`: Extract image properties, band definitions, spatial resolution, and CRS projection.
