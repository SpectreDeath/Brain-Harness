# Knowledge Item: Google Earth Engine Planetary Geospatial Processing & Domain Partitioning

## Summary
Google Earth Engine (`earthengine-api` @ commit `69cb225`) represents the state of the art in planetary-scale satellite data analysis, environmental monitoring, and geospatial computing.

## Core Architectural Invariants Bridged into Brain Harness

### 1. Deferred Server-Side Evaluation
Earth Engine client classes (`ee.Image`, `ee.ImageCollection`, `ee.FeatureCollection`, `ee.Reducer`) act as AST builders. They do not execute computations locally, but serialize operation DAGs into JSON structures dispatched to Google Cloud workers. This pattern bounds local process memory and allows agents to reason about multi-terabyte rasters without local bandwidth bottlenecks.

### 2. Domain-Partitioned Seam Isolation (Rule 18)
To prevent monolithic SDK sprawl, Earth Engine is bridged into two single-responsibility plugins:
- `plugin.earth_engine_imagery`: Specialized in satellite imagery collections, multi-spectral band index computation (NDVI, NDWI, EVI, NBR), temporal compositing, and visualization thumbnails.
- `plugin.earth_engine_spatial_analytics`: Specialized in polygon zonal statistics, digital elevation model (DEM) terrain modeling (slope, aspect, hillshade), vector feature querying, and asynchronous batch task management.

### 3. Subprocess Sandboxing & Deterministic Offline Fallbacks (Rules 5, 7, 14)
- Subprocess isolation ensures third-party cloud SDK dependencies cannot compromise the core Harness micro-kernel.
- Async pipe transports are cleanly drained and closed in `finally` blocks to guarantee OS resource safety.
- An adaptive dual-mode execution layer ensures offline deterministic calculations (GeoJSON intersections, analytical spectral index formulas, Horn topographic convolutions, and catalog indexing) when live Google Cloud credentials are not configured, guaranteeing hermetic test execution.
