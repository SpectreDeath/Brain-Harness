---
name: gods-eye-view
description: "Execute planetary OSINT reconnaissance, multi-layer spatial analytics, live telemetry queries, and 3D globe rendering using the God's Eye View engine across 5 domain subgroups. Do not use for unauthorized tracking, kinetic targeting, or military operations."
category: geospatial_and_osint
version: "1.0.0"
---

# God's Eye View Planetary Intelligence & OSINT Skill

Provides authoritative operational guidance, domain workflows, and safety guardrails for the God's Eye View (`plugin.gods_eye_view`, `harness gev`) engine across its 24 tools and 5 domain subgroups.

## Architecture & Subgroup Organization

1. **Analyst & Situation Briefs** (`harness gev brief`):
   - Computes multi-domain regional overlays combining active flights, vessels, earthquakes, thermal anomalies, and weather.
   - Fallback profile: Pure offline execution using the spatial index and cached telemetry when disconnected.
2. **Aviation & Maritime Telemetry** (`harness gev flights`, `harness gev vessels`):
   - ADS-B transponder vectors via OpenSky/ADS-B Exchange protocols and AIS vessel positions.
   - Cache TTL: 15 seconds for flights, 30 seconds for vessels.
   - Fallback profile: Generates schema-compliant simulated vectors when network air-gap is active.
3. **Environmental & Hazards** (`harness gev hazards`):
   - USGS real-time seismic feeds, NASA FIRMS active wildfire hotspots, and Open-Meteo meteorological conditions.
4. **Tactical, Space & Infrastructure** (`harness gev spatial`):
   - SGP4 orbital overpass calculation for low-Earth orbit satellites (ISS, Starlink).
   - Global submarine fiber cables, cable landing stations, and hyperscale datacenters.
5. **Geospatial & 3D Globe Rendering** (`harness gev render`):
   - Headless CesiumJS globe snapshots, Google 3D Map Tiles satellite orthomosaics, and Street View 360-degree heading captures via `NodeCliBridge`.

## Provenance & Data Freshness Invariant

Every God's Eye View response emits a provenance envelope containing:
- `source_mode`: One of `live` (fresh network telemetry), `cached` (within TTL window), or `simulated_fallback` (air-gap simulation).
- `fetched_at_utc`: ISO-8601 UTC timestamp.
- `ttl_seconds`: Numeric validity window.
- `fallback_reason`: Explanation if simulated data was returned.

The agent must explicitly communicate `source_mode` and timestamps to the user. Never describe simulated or cached data as confirmed live telemetry.

## CLI Usage Quick Reference

```bash
# Runtime environment probe
harness gev status --json

# Regional situation brief
harness gev brief --lat 37.7749 --lon -122.4194 --radius-km 100 --json

# Live flights around an area
harness gev flights --lat 40.7128 --lon -74.0060 --radius-km 150 --callsign UAL --json

# Maritime AIS vessels
harness gev vessels --lat 1.3521 --lon 103.8198 --radius-km 50 --json

# Environmental hazards
harness gev hazards --lat 35.6762 --lon 139.6503 --kind earthquakes --json

# Satellite pass prediction
harness gev spatial --lat 51.5074 --lon -0.1278 --kind sat-passes --json

# Render 3D Cesium globe snapshot
harness gev render --lat 37.7749 --lon -122.4194 --mode globe --output ./globe_sf.png
```

## Visual Brief

When executing regional queries or generating situation overviews, God's Eye View can render self-contained dark-theme HTML briefs and 3D globe visualization summaries:
- **Brief Delivery**: Rendered to `%TEMP%/gev-brief-<timestamp>.html` containing interactive satellite and terrain overlays.
- **Visual Verification**: Review flight tracks, vessel density, and seismic clusters before passing findings to downstream agents.

## Mandatory Checkpoints

- **RequestFeedback**: Before executing high-resolution 3D tile orthomosaic stitches or large-radius global searches exceeding default budgets, pause and request feedback with proposed bounding box and estimated tile count.
- **Air-Gap Verification**: Verify `source_mode` badge on all telemetry observations before reporting findings; never claim real-time accuracy for simulated or cached fallback data.

## Anti-Patterns

- **Simulated-As-Live Hallucination** — Presenting simulated fallback telemetry or cached records as confirmed live real-world observations.
- **Unbounded Global Spatial Scans** — Executing radius queries exceeding operational budgets without bounding boxes or spatial index pruning.
- **Stale Observation Extrapolation** — Treating a single flight or vessel transponder ping as a continuous real-time coordinate without noting elapsed latency.
- **Frontend UI Injection** — Attempting to inject live Cesium WebGL widgets into static UI dashboard bundles rather than exporting discrete image/HTML artifacts.
- **Air-Gap Network Leakage** — Bypassing offline simulation fallbacks to force unauthorized external network connections when `HARNESS_NO_NETWORK=1` is configured.

## Related Resources

- [Summary Card](CARD.md) — Quick reference card and invariants checklist.
- [Open Source GIS Architect](../open-source-gis-architect/SKILL.md) — Open source spatial processing.
- [Geospatial Disaster Simulation](../geospatial-disaster-simulation/SKILL.md) — Three.js geospatial disaster simulation.
