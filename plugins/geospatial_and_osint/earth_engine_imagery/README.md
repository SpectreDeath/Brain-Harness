# Google Earth Engine Imagery Plugin

`plugin.earth_engine_imagery` bridges satellite image discovery, multi-spectral index calculation (NDVI, NDWI, EVI, NBR), temporal compositing, and visual thumbnail generation into Brain Harness.

## Architecture

- **Domain Category**: `plugins/geospatial_and_osint/` (Rule 18)
- **Isolation Mode**: `SUBPROCESS` (Rule 5 & Rule 7)
- **Service Key**: `service.earth_engine_imagery` (`EarthEngineImageryService`, Rule 2)
- **Single-Seam Resolver**: `resolve_earth_engine_imagery(context)` (Rule 58)
- **Plugin Module Singleton**: `plugin = EarthEngineImageryPlugin()` (Rule 45)

## Subpackage Decomposition (`engine/`)

- `engine/models.py`: Slotted domain models (`SceneMetadata`, `SpectralIndexResult`, `CompositeResult`, `ThumbnailResult`, `ImageDescription`, Rule 12 & Rule 43).
- `engine/protocols.py`: `EarthEngineImageryService` protocol and `EARTH_ENGINE_IMAGERY_KEY`.
- `engine/core.py`: Lazy EE initialization, path detection, and authentication hooks.
- `engine/search.py`: `ImageSearchMixin` implementing `search_image_collection` and `describe_image`.
- `engine/spectral.py`: `SpectralProcessingMixin` implementing `compute_spectral_index`.
- `engine/temporal.py`: `TemporalCompositingMixin` implementing `composite_timeseries` and `get_image_thumbnail_url`.
- `engine/service.py`: `EarthEngineImageryEngine` composite coordinator.
- `engine/resolvers.py`: Single-seam resolver with process default fallback.

## Available Tools

1. `ee_search_image_collection`: Filter satellite collections (Sentinel-2, Landsat, MODIS) by bounding box, date range, and maximum cloud cover.
2. `ee_compute_spectral_index`: Compute NDVI, NDWI, EVI, NBR, or custom band expressions.
3. `ee_composite_timeseries`: Generate multi-temporal composites (median, mean, min, max, greenest pixel) with cloud masking.
4. `ee_get_image_thumbnail_url`: Generate visual preview thumbnail URLs and map tile endpoints.
5. `ee_describe_image`: Extract image properties, band definitions, spatial resolution, and CRS projection.
