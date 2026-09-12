# plugin.gods_eye_view (v0.1.0)

Planetary intelligence, real-time OSINT feeds, spatial analytics engine, and 3D globe rendering

---

## Overview & Metadata

- **Plugin Directory**: `plugins/geospatial_and_osint/gods_eye_view`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `gev_analyst_query` | `(layer, filters, lat, lon, radius_km, bbox, follow_up_token)` | Execute multi-layer spatial queries, compound filters, and aggregations across flights, vessels, fires, and earthquakes |
| `gev_fetch_live_flights` | `(bbox, icao24, callsign, military_only, limit)` | Fetch live aviation transponder vectors with altitude, velocity, and military designation |
| `gev_fetch_ais_vessels` | `(bbox, mmsi, ship_type, destination, limit)` | Retrieve real-time maritime AIS vessel records with coordinates, heading, and deadweight cargo class |
| `gev_fetch_earthquakes` | `(min_magnitude, timeframe, lat, lon, radius_km)` | Query USGS live seismic telemetry feeds for tectonic activity, depth, and tsunami alerts |
| `gev_fetch_firms_hotspots` | `(bbox, min_frp, source, days)` | Fetch NASA FIRMS satellite thermal anomalies and active wildfire perimeters with Fire Radiative Power (MW) |
| `gev_query_military_awareness` | `(lat, lon, radius_km, include_bases)` | Compute tactical military awareness corridor: airborne fighters/transports, naval contacts, and proximity to military installations |
| `gev_calculate_satellite_passes` | `(lat, lon, sat_name, norad_id, horizon_hours)` | Predict upcoming orbital passes (ISS, Starlink, reconnaissance) over specified ground coordinates |
| `gev_query_infrastructure` | `(infra_type, query, lat, lon, radius_km)` | Query offline global submarine fiber cables, landing stations, hyperscale datacenters, dams, and defense installations |
| `gev_render_sat_ortho` | `(lat, lon, zoom, size, outdir)` | Stitch high-resolution satellite orthomosaic imagery from Google 3D Map Tiles with Ground Sample Distance georeferencing |
| `gev_capture_streetview_headings` | `(lat, lon, fov, pitch, neighbors, outdir)` | Capture 8 compass headings (360 ground view) at target coordinates with optional street graph neighbor crawling |
| `gev_render_globe_snapshot` | `(lat, lon, altitude_m, pitch, heading, style, outdir)` | Render photorealistic 3D Cesium globe snapshots with post-processing shaders (thermal, surveillance, noir, snow) |

---

## Key Modules & AST Symbols

### Module [`async_runner.py`](async_runner.py)

Thread-Safe Async/Sync Execution Seam for Tool Handlers.

Prevents `RuntimeError: This event loop is already running` when synchronous tool
functions are invoked inside active asyncio event loops or agent runtimes.

#### Functions

- `def run_sync_safe(coro) -> T`
  - Execute a coroutine synchronously without crashing if an event loop is already active.


### Module [`cli_bridge.py`](cli_bridge.py)

Subprocess bridge for Node.js geospatial imaging and 3D globe rendering scripts.

Wraps tools/ scripts from gods-eye-view:
- sat-ortho.mjs (Google 3D Map Tiles satellite orthomosaic stitcher)
- streetview-headings.mjs (360 multi-heading Street View capture)
- streetview-panorama.mjs (High-res equirectangular panorama stitcher)
- pano-pinhole.mjs (Pinhole perspective reprojector)
- cesium-render.mjs (Headless Puppeteer Cesium 3D globe renderer)

#### Classes

- `class NodeCliBridge`
  Safe subprocess invoker for upstream Node.js scripts.
  - `def __init__(tools_dir) -> None`
  - `def is_node_available() -> bool`
  - `def render_sat_ortho(lat, lon, zoom, size, outdir) -> ImageryRenderResult`
  - `def capture_streetview_headings(lat, lon, fov, pitch, neighbors, outdir) -> ImageryRenderResult`
  - `def render_globe_snapshot(lat, lon, altitude_m, pitch, heading, style, outdir) -> ImageryRenderResult`


### Module [`engine.py`](engine.py)

Core Planetary OSINT, Geospatial Intelligence, and Analyst Query Engine.

Deepened Architecture:
- Tiered, single-flight TelemetryCache for all live API streams
- 2D SpatialHashGrid index for sub-millisecond bounding box and radius queries
- Declarative SpatialQueryPipeline with compound predicates and RFC 7946 GeoJSON export
- Bounded QuerySessionStore for conversational follow-up memory

#### Classes

- `class GodsEyeViewEngine`
  Stateful geospatial intelligence and multi-layer query engine.
  - `def __init__(data_dir) -> None`
  - `def fetch_flights(bbox, icao24, callsign, military_only, limit, force_refresh) -> list[FlightRecord]`
  - `def fetch_vessels(bbox, mmsi, ship_type, destination, limit) -> list[VesselRecord]`
  - `def fetch_earthquakes(min_magnitude, timeframe, lat, lon, radius_km, limit, force_refresh) -> list[EarthquakeRecord]`
  - `def fetch_firms_hotspots(bbox, min_frp, source, days, limit) -> list[ThermalHotspotRecord]`
  - `def query_military_awareness(lat, lon, radius_km, include_bases) -> MilitaryAwarenessSummary`
  - `def calculate_satellite_passes(lat, lon, sat_name, norad_id, horizon_hours) -> list[SatellitePassRecord]`
  - `def query_infrastructure(infra_type, query, lat, lon, radius_km, limit) -> list[InfrastructureRecord]`
  - `def query_analyst(layer, filters, lat, lon, radius_km, bbox, polygon, follow_up_token, include_geojson) -> AnalystQueryResult`


#### Functions

- `def asyncio_wrap(val) -> T`
  - Helper to wrap static object as async return.


### Module [`infrastructure_store.py`](infrastructure_store.py)

Offline Critical Infrastructure asset store and spatial indexing engine.

Supports submarine fiber optic cables, landing stations, hyperscale datacenters,
dams, reservoirs, and curated defense installations indexed via SpatialHashGrid.

#### Classes

- `class InfrastructureStore`
  Indexed catalog of global infrastructure assets backed by SpatialHashGrid.
  - `def __init__(external_data_dir) -> None`
  - `def query(infra_type, search_query, lat, lon, radius_km, limit) -> list[InfrastructureRecord]`


### Module [`main.py`](main.py)

God's Eye View Plugin & HarnessPlugin Service Implementation.

#### Classes

- `class GodsEyeViewPlugin`
  Harness Plugin implementing GodsEyeViewService and registering GODS_EYE_VIEW_SERVICE_KEY.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def query_analyst(layer, filters, lat, lon, radius_km, bbox, follow_up_token) -> AnalystQueryResult`
  - `def fetch_flights(bbox, icao24, callsign, military_only, limit) -> list[FlightRecord]`
  - `def fetch_vessels(bbox, mmsi, ship_type, destination, limit) -> list[VesselRecord]`
  - `def fetch_earthquakes(min_magnitude, timeframe, lat, lon, radius_km) -> list[EarthquakeRecord]`
  - `def fetch_firms_hotspots(bbox, min_frp, source, days) -> list[ThermalHotspotRecord]`
  - `def query_military_awareness(lat, lon, radius_km, include_bases) -> MilitaryAwarenessSummary`
  - `def calculate_satellite_passes(lat, lon, sat_name, norad_id, horizon_hours) -> list[SatellitePassRecord]`
  - `def query_infrastructure(infra_type, query, lat, lon, radius_km) -> list[InfrastructureRecord]`
  - `def render_sat_ortho(lat, lon, zoom, size, outdir) -> ImageryRenderResult`
  - `def capture_streetview_headings(lat, lon, fov, pitch, neighbors, outdir) -> ImageryRenderResult`
  - `def render_globe_snapshot(lat, lon, altitude_m, pitch, heading, style, outdir) -> ImageryRenderResult`


#### Functions

- `def gev_analyst_query(layer, filters, lat, lon, radius_km, bbox, follow_up_token) -> dict[str, Any]`
  - Execute multi-layer spatial queries, compound filters, and aggregations across flights, vessels, fires, and earthquakes.
- `def gev_fetch_live_flights(bbox, icao24, callsign, military_only, limit) -> list[dict[str, Any]]`
  - Fetch live aviation transponder vectors with OpenSky / ADSB-lol fallback.
- `def gev_fetch_ais_vessels(bbox, mmsi, ship_type, destination, limit) -> list[dict[str, Any]]`
  - Retrieve real-time maritime AIS vessel records.
- `def gev_fetch_earthquakes(min_magnitude, timeframe, lat, lon, radius_km) -> list[dict[str, Any]]`
  - Query USGS live seismic telemetry.
- `def gev_fetch_firms_hotspots(bbox, min_frp, source, days) -> list[dict[str, Any]]`
  - Fetch NASA FIRMS thermal hotspots and active wildfire perimeters.
- `def gev_query_military_awareness(lat, lon, radius_km, include_bases) -> dict[str, Any]`
  - Compute tactical military awareness corridor and air/naval assets.
- `def gev_calculate_satellite_passes(lat, lon, sat_name, norad_id, horizon_hours) -> list[dict[str, Any]]`
  - Predict upcoming orbital overpasses over ground coordinates.
- `def gev_query_infrastructure(infra_type, query, lat, lon, radius_km) -> list[dict[str, Any]]`
  - Query offline global submarine cables, datacenters, dams, and POIs.
- `def gev_render_sat_ortho(lat, lon, zoom, size, outdir) -> dict[str, Any]`
  - Stitch high-resolution satellite orthomosaic from 3D Map Tiles.
- `def gev_capture_streetview_headings(lat, lon, fov, pitch, neighbors, outdir) -> dict[str, Any]`
  - Capture 8 compass headings (360 ground view) via Static Street View.
- `def gev_render_globe_snapshot(lat, lon, altitude_m, pitch, heading, style, outdir) -> dict[str, Any]`
  - Render photorealistic 3D Cesium globe snapshots with post-processing shaders.


### Module [`models.py`](models.py)

Pydantic v2 data models for God's Eye View plugin entities.

#### Classes

- `class FlightRecord`
  Real-time aviation transponder record.
- `class VesselRecord`
  Real-time maritime AIS vessel record.
- `class EarthquakeRecord`
  Seismic telemetry event record from USGS.
- `class ThermalHotspotRecord`
  NASA FIRMS satellite thermal anomaly record.
- `class SatellitePassRecord`
  Computed orbital overpass for a satellite over ground coordinates.
- `class MilitaryContact`
  Identified military air, naval, or radar contact.
- `class MilitaryAwarenessSummary`
  Military intelligence summary within a tactical corridor.
- `class InfrastructureRecord`
  Global critical infrastructure asset.
- `class AnalystQueryResult`
  Result of multi-layer spatial query engine execution.
- `class ImageryRenderResult`
  Result of geospatial imagery generation or 3D rendering.


### Module [`query_pipeline.py`](query_pipeline.py)

Composable Spatial Query Pipeline and RFC 7946 GeoJSON Exporter.

Executes structured multi-layer spatial filtering, compound attribute predicates,
statistical aggregations, and standard GeoJSON transformations.

#### Classes

- `class SpatialQueryPipeline`
  Analytical pipeline for spatial datasets and OSINT telemetry.
  - `def apply_predicate(val, op, target) -> bool`
  - `def filter_records(cls, records, filters, lat, lon, radius_km, bbox, polygon) -> list[dict[str, Any]]`
  - `def compute_aggregations(records) -> dict[str, Any]`
  - `def to_geojson(records, layer_name) -> dict[str, Any]`
- `class QuerySessionStore`
  Manages ephemeral conversational query session memory.
  - `def __init__(max_sessions, session_ttl_sec) -> None`
  - `def save_session(records) -> str`
  - `def get_session(token) -> list[dict[str, Any]] | None`


### Module [`spatial_index.py`](spatial_index.py)

2D Spatial Hash Grid Index for high-performance geospatial queries.

Partitions geographical coordinates into degree-based spatial buckets, accelerating
proximity, radius, k-nearest neighbors (k-NN), and bounding box queries from O(N)
to O(1) candidate lookups.

#### Classes

- `class SpatialHashGrid`
  2D spatial grid partitioning coordinates into degree buckets.
  - `def __init__(cell_size_deg, lat_extractor, lon_extractor) -> None`
  - `def insert(item, lat, lon, key) -> None`
  - `def bulk_insert(items, key_fn) -> None`
  - `def remove(key) -> bool`
  - `def clear() -> None`
  - `def query_radius(lat, lon, radius_km) -> list[tuple[float, T]]`
  - `def query_bbox(north, south, west, east) -> list[T]`
  - `def query_knn(lat, lon, k, max_radius_km) -> list[tuple[float, T]]`
  - `def query_polygon(vertices) -> list[T]`


#### Functions

- `def haversine_km(lat1, lon1, lat2, lon2) -> float`
  - Calculate Great-Circle distance between two coordinates in kilometers.
- `def point_in_polygon(lat, lon, vertices) -> bool`
  - Ray casting algorithm for testing if a point (lat, lon) is inside a polygon.


### Module [`telemetry_cache.py`](telemetry_cache.py)

Thread-safe Asynchronous Telemetry Cache with Single-Flight Stampede Protection.

Provides tiered time-to-live (TTL) expiration, automatic stale-while-revalidate,
and single-flight locking to prevent downstream API rate limiting across agent workflows.

#### Classes

- `class CacheEntry`
  Cached payload with timestamp metadata.
- `class TelemetryCache`
  Thread-safe async TTL cache for high-frequency geospatial feeds.
  - `def __init__(stale_ratio) -> None`
  - `def get_or_fetch(key, fetch_fn, ttl_seconds, force_refresh) -> T`
  - `def get_cached_nowait(key) -> T | None`
  - `def invalidate(key) -> bool`
  - `def clear() -> None`
  - `def get_stats() -> dict[str, Any]`


### Module [`test_gods_eye_view.py`](test_gods_eye_view.py)

Comprehensive test suite for God's Eye View plugin, spatial index, and query pipeline.

#### Functions

- `def test_haversine_and_point_in_polygon() -> None`
- `def test_spatial_hash_grid_operations() -> None`
- `def test_telemetry_cache_single_flight_and_ttl() -> None`
- `def test_spatial_query_pipeline_predicates_and_aggregations() -> None`
- `def test_query_session_store() -> None`
- `def test_async_runner_safe_execution() -> None`
- `def test_async_runner_inside_active_event_loop() -> None`
- `def test_engine_fetch_flights_and_caching() -> None`
- `def test_engine_fetch_vessels_and_earthquakes() -> None`
- `def test_engine_military_awareness_and_satellite_passes() -> None`
- `def test_infrastructure_store_query_with_spatial_grid() -> None`
- `def test_analyst_query_pipeline_and_geojson() -> None`
- `def test_standalone_tools_with_async_runner() -> None`
- `def test_plugin_lifecycle_and_di() -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
