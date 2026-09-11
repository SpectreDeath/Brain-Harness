# Explanation: Earth Engine Architecture, Seams & Sandbox Design

Architectural context, design trade-offs, and principles governing the integration of Google Earth Engine into Brain Harness.

---

## 1. Client-Side Expression DAGs vs. Server-Side Planetary Compute

Google Earth Engine uses a fundamentally different computational model than local NumPy or GDAL raster pipelines:
1. **Deferred / Lazy Execution**: Instantiating `ee.Image` or `ee.ImageCollection` does not load satellite pixels into Python memory. Instead, it constructs a directed acyclic graph (DAG) of functional operations represented as JSON expressions.
2. **Server-Side Parallelism**: Pixel computation happens on Google's cloud infrastructure when triggered by `.getInfo()`, thumbnail requests, or batch export tasks.
3. **Pyramidal Multi-Scale Tiling**: Earth Engine maintains pre-computed image pyramids at varying zoom levels. Reducers and spatial aggregations compute at the requested nominal scale rather than downloading full-resolution gigabyte scenes.

---

## 2. Rationale for Domain Partitioning (Rule 18)

The monolithic `earthengine-api` library combines raster processing, vector topology, deep-learning model bridges, asset permissions, and cloud task schedulers into a single namespace. 

Bridging this entire surface into an omnibus plugin violates **Rule 18 (Domain-Partitioned Plugin Synthesis)**:
- Raster imagery analysis requires specialized parameter handling (spectral band lists, cloud masks, reflectance stretching).
- Vector analytics and zonal statistics require polygon geometry parsing, reduction statistics, and topographic math.
- Splitting the tools into `plugin.earth_engine_imagery` and `plugin.earth_engine_spatial_analytics` guarantees high modularity, independent testing, and fine-grained agent tool approval boundaries.

---

## 3. Subprocess Sandbox & Pipe Transport Disposal (Rule 5 & Rule 14)

External libraries interacting with cloud APIs must run under subprocess isolation:
- **Crash Isolation**: Segmentation faults or unhandled C-extension crashes within GIS bindings cannot take down the core Harness proactor.
- **Resource Cleanup**: Subprocess workers communicate via JSON-RPC pipes that are explicitly drained and closed inside `finally` blocks (Rule 14), preventing descriptor leaks on Windows proactor event loops.
- **Lazy Staging (Rule 7)**: External environments remain in `DISCOVERED` status during startup, provisioning dependencies lazily on first invocation.

---

## 4. Dual-Mode Execution: Live Cloud RPC vs. Deterministic Local Simulation

Autonomous agent workflows frequently run in CI pipelines, air-gapped environments, or evaluation environments without live Google Cloud authentication.
The plugins implement an adaptive architecture:
- When Google Cloud credentials exist and `ee.Initialize()` succeeds, calls delegate directly to live Earth Engine endpoints.
- When unauthenticated, the engine executes deterministic local calculations (e.g. geometric bounding box filtering, analytical spectral index formulas, Horn 8-neighbor topographic convolution, and catalog metadata indexing).
- This guarantees 100% green test execution, zero cold-start timeouts, and reproducible agent evals.
