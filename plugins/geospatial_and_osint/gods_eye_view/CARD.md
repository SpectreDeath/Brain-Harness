# God's Eye View Planetary OSINT & Spatial Intelligence Plugin

`plugin.gods_eye_view` brings planetary-scale real-time open source intelligence (OSINT), spatial telemetry feeds, offline critical infrastructure queries, and 3D globe visualization into the Brain Harness agent ecosystem.

## Architecture

- **Isolation**: `IsolationMode.SUBPROCESS`
- **Service Key**: `ServiceKey[GodsEyeViewService]("service.gods_eye_view")`
- **Category**: `geospatial_and_osint`
- **Upstream Source**: `gods-eye-view` (`D:\GitHub\cloned\gods-eye-view-main`)

```
[Agent Query / Prompt]
         │
         ▼
[GodsEyeViewService (ServiceKey)]
         │
 ┌───────┴────────────────────────┬─────────────────────────┐
 │                                │                         │
 ▼                                ▼                         ▼
[OSINT Live Feeds]       [Analyst Spatial Engine]   [Node/Cesium Imaging Bridge]
 • OpenSky / ADS-B        • Haversine & Bounding Box • sat-ortho.mjs
 • AIS Live Vessels       • Compound Filters         • streetview-headings.mjs
 • USGS Earthquakes       • Aggregations & Grouping  • cesium-render.mjs
 • NASA FIRMS Hotspots    • Follow-up Memory Tokens  • Pinhole Reprojection
 • Orbital TLE Passes     • Critical Infra Catalog
```

## Available Tools

| Tool | Signature Summary | Description |
| :--- | :--- | :--- |
| `gev_analyst_query` | `layer, filters?, lat?, lon?, radius_km?, bbox?, follow_up_token?` | Multi-layer spatial query engine with compound filters, aggregations, and session memory |
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

## Usage Examples

### 1. Spatial Analyst Query Across Flights
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
```

### 2. Querying Military Proximity & Assets
```python
summary = await gev.query_military_awareness(
    lat=49.4369,
    lon=7.6003, # Near Ramstein Air Base
    radius_km=100.0,
)
print(f"Threat Level: {summary.threat_level}, Air Contacts: {len(summary.air_contacts)}")
```

### 3. Critical Infrastructure Spatial Lookup
```python
cables = gev.query_infrastructure(
    infra_type="submarine_cable",
    query="MAREA",
)
print(f"Cable: {cables[0].name}, Capacity: {cables[0].properties.get('capacity_tbps')} Tbps")
```
