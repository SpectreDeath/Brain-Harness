# How-To: Use the God's Eye View Planetary Intelligence Toolkit

This guide covers the command-line interface, domain subgroups, offline simulation profiles, and operational boundaries of the God's Eye View (`plugin.gods_eye_view`, `harness gev`) toolkit.

---

## 1. Overview & Architectural Subgroups

The God's Eye View toolkit integrates 24 planetary reconnaissance and OSINT capabilities partitioned into 5 domain subgroups:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GOD'S EYE VIEW ARCHITECTURE                     │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Analyst & Briefs      │ Situation briefs, compound spatial filters  │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Aviation & Maritime   │ ADS-B flights, AIS vessels, track histories │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 3. Hazards & Environment │ USGS earthquakes, FIRMS fires, weather      │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 4. Tactical & Space      │ SGP4 satellite passes, submarine cables     │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 5. Geospatial Rendering  │ 3D Cesium globe, satellite orthomosaics     │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. CLI Command Reference

All subcommands are accessible via the canonical `harness gev` group and the declared aliases `harness gods-eye` and `harness osint`.

### Runtime Status & Environment Probe

```bash
harness gev status --json
```

Reports whether the Node.js rendering bridge is detected, the path to upstream tool scripts, and confirmation of offline simulation fallback.

### Situation Briefs

```bash
harness gev brief --lat 37.7749 --lon -122.4194 --radius-km 100
```

Generates a regional multi-domain overview aggregating aviation, maritime, and seismic observations.

### Aviation Telemetry

```bash
# Query flights with callsign substring
harness gev flights --lat 40.7128 --lon -74.0060 --radius-km 150 --callsign UAL

# Filter strictly for military or government aircraft
harness gev flights --lat 32.7157 --lon -117.1611 --radius-km 200 --military --json
```

### Maritime AIS Vessels

```bash
harness gev vessels --lat 1.3521 --lon 103.8198 --radius-km 50 --name Maersk --json
```

### Environmental Hazards & Weather

```bash
# Query earthquakes
harness gev hazards --lat 35.6762 --lon 139.6503 --kind earthquakes --radius-km 500

# Query active wildfire thermal hotspots
harness gev hazards --lat -33.8688 --lon 151.2093 --kind fires --radius-km 300
```

### Tactical, Space & Infrastructure Queries

```bash
# SGP4 orbital satellite pass prediction for ground coordinates
harness gev spatial --lat 51.5074 --lon -0.1278 --kind sat-passes

# Submarine cables and datacenter infrastructure
harness gev spatial --lat 25.2048 --lon 55.2708 --kind infra --query "cable"
```

### 3D Globe & Imagery Rendering

```bash
# Render photorealistic 3D Cesium globe snapshot
harness gev render --lat 37.7749 --lon -122.4194 --mode globe --output ./globe_sf.png

# Stitch high-resolution satellite orthomosaic
harness gev render --lat 48.8566 --lon 2.3522 --mode ortho --output ./ortho_paris.png
```

---

## 3. Data Freshness & Provenance Guarantees

Every tool execution emits an envelope with:
- `source_mode`: `live` (network HTTP/MCP telemetry), `cached` (within TTL window), or `simulated_fallback` (deterministic offline calculation).
- `fetched_at_utc`: Exact timestamp of acquisition.
- `ttl_seconds`: Validity window (15s for flights, 30s for vessels, 60s for earthquakes, 300s for wildfire hotspots).

---

## 4. Operational Boundaries

- **No Live UI Bundle Modifications**: 3D rendering outputs are saved strictly as standalone PNG, GeoJSON, or HTML files in user-designated directories; no static bundle injection into the core web dashboard.
- **Air-Gap First**: If external network access is unavailable (`HARNESS_NO_NETWORK=1`), the engine transparently returns simulated fallback payloads without raising unhandled connection exceptions.

