# God's Eye View Planetary OSINT & Spatial Intelligence Plugin

`plugin.gods_eye_view` delivers planetary-scale real-time open source intelligence (OSINT), high-performance spatial telemetry indexing, offline critical infrastructure lookups, and 3D globe visualization into the Brain Harness agent ecosystem.

## Deepened Architecture

- **Isolation Mode**: `IsolationMode.SUBPROCESS`
- **Service Key**: `ServiceKey[GodsEyeViewService]("service.gods_eye_view")`
- **Category**: `geospatial_and_osint`
- **Upstream Repository**: `gods-eye-view` (`D:\GitHub\cloned\gods-eye-view-main`)

```
[Agent Query / Workflow]
         │
         ▼
[GodsEyeViewService (ServiceKey)] ───► [run_sync_safe Executor]
         │
 ┌───────┴──────────────────────────────┬───────────────────────────────┐
 │                                      │                               │
 ▼                                      ▼                               ▼
[TelemetryCache (Tiered TTL)]   [SpatialHashGrid (2D Buckets)]   [SpatialQueryPipeline]
 • Flights (15s TTL)             • O(1) Candidate Cell Pruning    • Predicate AST (eq/gt/contains)
 • Vessels (30s TTL)             • k-NN Ring Expansion            • Statistical Aggregations
 • Earthquakes (60s TTL)         • Bounding Box & Polygon Filter  • RFC 7946 GeoJSON Exporter
 • NASA FIRMS (300s TTL)         • Subsea Cables & Datacenters    • Bounded Session Memory Store
 • Single-Flight Stampede Lock   • Dams & Defense Airbases
```

---

## Core Deep Modules

1. **`spatial_index.py` (`SpatialHashGrid[T]`)**:
   - 2D grid spatial partition dividing coordinates into degree-based buckets.
   - `query_radius(lat, lon, radius_km)`: Radius query with geodesic Haversine distance verification.
   - `query_bbox(north, south, west, east)`: Bounding box search across grid cells.
   - `query_knn(lat, lon, k)`: Concentric expanding ring search for k-nearest neighbors.
   - `query_polygon(vertices)`: Ray-casting polygon point-in-ring filter.

2. **`telemetry_cache.py` (`TelemetryCache[T]`)**:
   - Single-flight concurrency locking (`asyncio.Lock`) preventing upstream API rate limits (429).
   - Domain-specific TTLs with stale-while-revalidate background refresh and network error fallbacks.

3. **`query_pipeline.py` (`SpatialQueryPipeline`)**:
   - Composable multi-predicate engine (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `starts_with`, `in`, `between`, `regex`).
   - Statistical aggregator (`count`, `avg`, `min`, `max`, `sum`, categorical distributions).
   - `to_geojson()`: Standard RFC 7946 GeoJSON `FeatureCollection` generator.

4. **`async_runner.py` (`run_sync_safe`)**:
   - Universal event-loop-safe coroutine runner preventing `RuntimeError` across CLI scripts, synchronous tool executors, and active async agent loops.

---

## Available Tools

| Tool | Signature Summary | Capabilities |
| :--- | :--- | :--- |
| `gev_analyst_query` | `layer, filters?, lat?, lon?, radius_km?, bbox?, follow_up_token?` | Multi-layer spatial query engine with compound filters, aggregations, GeoJSON export, and session memory |
| `gev_fetch_live_flights` | `bbox?, icao24?, callsign?, military_only?, limit?` | Real-time aviation transponder vectors with speed, altitude, and military designation |
| `gev_fetch_ais_vessels` | `bbox?, mmsi?, ship_type?, destination?, limit?` | Live maritime AIS vessel telemetry with heading, speed, and cargo classification |
| `gev_fetch_earthquakes` | `min_magnitude?, timeframe?, lat?, lon?, radius_km?` | USGS real-time seismic feeds with epicenter, depth, and tsunami warnings |
| `gev_fetch_firms_hotspots` | `bbox?, min_frp?, source?, days?` | NASA FIRMS active wildfire hotspots and Fire Radiative Power (MW) |
| `gev_query_military_awareness` | `lat, lon, radius_km?, include_bases?` | Tactical military corridor evaluation with air/naval assets and airbase proximity |
| `gev_calculate_satellite_passes` | `lat, lon, sat_name?, norad_id?, horizon_hours?` | Computes upcoming satellite overpasses (ISS, Starlink) over ground coordinates |
| `gev_query_infrastructure` | `infra_type, query?, lat?, lon?, radius_km?` | Global submarine cables, landing stations, datacenters, dams, and installations |
| `gev_render_sat_ortho` | `lat, lon, zoom?, size?, outdir?` | High-res satellite orthomosaic stitcher from 3D Map Tiles with GSD metrics |
| `gev_capture_streetview_headings` | `lat, lon, fov?, pitch?, neighbors?, outdir?` | 8-compass-heading (360° ground view) capture with street graph traversal |
| `gev_render_globe_snapshot` | `lat, lon, altitude_m?, pitch?, heading?, style?` | Photorealistic 3D Cesium globe snapshots with post-processing shaders |

---

## Usage Examples

### 1. Spatial Analyst Query with RFC 7946 GeoJSON Export
```python
from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY

gev = context.resolve(GODS_EYE_VIEW_SERVICE_KEY)
result = await gev.query_analyst(
    layer="flights",
    filters=[{"field": "altitude_m", "op": "gt", "value": 10000}],
    lat=38.8951,
    lon=-77.0364,
    radius_km=150.0,
)
print(f"Matched {result.total_matched} high-altitude flights in corridor")
# Directly send standard GeoJSON to map viewers
geojson_payload = result.geojson
```

### 2. Tactical Military Awareness Corridor
```python
summary = await gev.query_military_awareness(
    lat=49.4369,
    lon=7.6003, # Ramstein Air Base region
    radius_km=100.0,
)
print(f"Threat Level: {summary.threat_level}, Air Contacts: {len(summary.air_contacts)}")
```
