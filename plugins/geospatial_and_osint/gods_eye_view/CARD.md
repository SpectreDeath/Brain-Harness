# Skill Summary Card: `gods_eye_view`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        gods_eye_view                            │
│ Category:    geospatial_and_osint                      │
│ Invocation:  service.gods_eye_view                     │
│ Version:     0.1.0                                     │
│ Isolation:   subprocess                                │
│ Upstream:    D:\GitHub\cloned\gods-eye-view            │
│ Provides:    "service.gods_eye_view"                   │
├────────────────────────────────────────────────────────┤
│ Target:      Planetary-scale OSINT, spatial indexing,  │
│              critical infrastructure lookups, and      │
│              photorealistic 3D globe visualization.    │
└────────────────────────────────────────────────────────┘
```

---

## Deepened Architecture

- **Isolation Mode**: `IsolationMode.SUBPROCESS`
- **Service Key**: `ServiceKey[GodsEyeViewService]("service.gods_eye_view")`
- **Category**: `geospatial_and_osint`
- **Upstream Repository**: `D:\GitHub\cloned\gods-eye-view` (Commit `591f299`)

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
 • Single-Flight Stampede Lock   • Dams & 36k+ Military Bases
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

3. **`infrastructure_store.py` (`InfrastructureStore`)**:
   - Indexed catalog of global infrastructure assets backed by `SpatialHashGrid`.
   - Ingests real local datasets from `D:\GitHub\cloned\gods-eye-view\src\data\local_data`: TeleGeography subsea cables, landing stations, hyperscale datacenters, hydroelectric dams, and 36,000+ OSM military installations.

4. **`cli_bridge.py` (`NodeCliBridge`)**:
   - Headless subprocess invoker for upstream Node.js rendering tools (`sat-ortho.mjs`, `streetview-headings.mjs`, `cesium-render.mjs`) and MCP stdio server JSON-RPC.

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
| `gev_get_weather` | `place?, lat?, lon?` | Current meteorological conditions (temperature, humidity, wind, sky condition) |
| `gev_get_weather_map` | `map_type?, place?, bbox?, lat?, lon?, radius_km?` | Animated radar and infrared satellite clouds overlay product |
| `gev_find_cctv_cameras` | `place?, bbox?, lat?, lon?, radius_km?, limit?` | Public traffic and municipal camera directory search |
| `gev_get_cctv_snapshot` | `camera_id` | Still visual snapshot frame from target camera installation |
| `gev_find_aircraft` | `callsign?, icao24?, registration?, limit?` | Worldwide aircraft locator by callsign, ICAO hex, or tail registration |
| `gev_get_aircraft_track` | `icao24, military?` | Historical 4D flight path track and position sequence |
| `gev_find_vessel` | `mmsi?, imo?, name?, limit?` | Global ship lookup by MMSI, IMO number, or vessel name substring |
| `gev_get_vessel_track` | `mmsi` | Historical maritime AIS position trail and movement history |
| `gev_situation_brief` | `place?, bbox?, lat?, lon?, radius_km?` | Composite multi-domain tactical intelligence overview for an area |
| `gev_get_terrain_height` | `points` | High-resolution elevation queries above mean sea level |
| `gev_get_cyclones` | `place?, bbox?, lat?, lon?, radius_km?` | Active tropical cyclone and hurricane advisories with pressure and wind speeds |
| `gev_get_active_fires` | `place?, bbox?, lat?, lon?, radius_km?, limit?` | Active wildfire detection perimeters with Fire Radiative Power (MW) |
| `gev_get_recent_imagery` | `place?, bbox?, lat?, lon?, radius_km?` | NASA/ESA Landsat and Sentinel-2 satellite imagery metadata and acquisition |

---

## Mandatory Invariants Checklist

- [ ] **Downward-Only Independence**: Tool execution must not depend on GUI, DOM, or Cesium browser globals.
- [ ] **Offline Spatial Resilience**: Critical infrastructure and military awareness queries must resolve offline via SpatialHashGrid when external network APIs are restricted.
- [ ] **Single-Flight Cache Concurrency**: Concurrent requests for the same telemetry layer must collapse to a single upstream network fetch.
- [ ] **Safe Event Loop Delegation**: Synchronous callers must execute through `run_sync_safe` to avoid nested event loop deadlocks.
- [ ] **Dual-File Knowledge Integrity**: Knowledge items distilled from the repository must persist as canonical dual-file directories (`metadata.json` + `summary.md`).
