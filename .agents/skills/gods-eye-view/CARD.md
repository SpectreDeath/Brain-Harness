# Skill Summary Card: `gods-eye-view`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        gods-eye-view                            │
│ Category:     geospatial_and_osint                     │
│ Invocation:   /gods-eye-view                           │
│ Trigger:      "planetary osint", "live flights",       │
│               "ais vessels", "earthquake telemetry",   │
│               "satellite pass prediction", "cctv osint"│
│ Version:      1.0.0                                    │
│ Requires:     "open-source-gis-architect"              │
│ Provides:     "gods_eye_view", "planetary_intelligence"│
├────────────────────────────────────────────────────────┤
│ Target:       Planetary OSINT queries, live telemetry  │
│               feeds, tactical spatial analytics, and   │
│               3D globe visual rendering across 5 tiers │
└────────────────────────────────────────────────────────┘
```

---

## The 5 Domain Subgroups

| Subgroup | Core Tools | Primary Artifact | Fallback Profile |
|---|---|---|---|
| **1. Analyst & Briefs** | `gev_analyst_query`, `gev_situation_brief` | Multi-domain situation brief | Offline spatial index fallback |
| **2. Aviation & Maritime** | `fetch_live_flights`, `fetch_ais_vessels`, `get_track` | ADS-B / AIS transponder vectors | Deterministic simulation fallback |
| **3. Environmental** | `fetch_earthquakes`, `fetch_firms_hotspots`, `get_weather` | USGS / FIRMS hazard summaries | Cached telemetry fallback |
| **4. Tactical & Space** | `query_infrastructure`, `calculate_satellite_passes` | Infrastructure & SGP4 passes | Pure Python offline execution |
| **5. 3D Rendering** | `render_sat_ortho`, `capture_streetview`, `globe_snapshot`| Rendered PNG / HTML asset | Simulated render descriptor |

---

## Mandatory Invariants Checklist

- [ ] **Provenance & Freshness Badge**: Every output payload must disclose `source_mode` (`live`, `cached`, `simulated_fallback`), `fetched_at_utc`, and `ttl_seconds`.
- [ ] **Stale Observation Disclosure**: Aviation and maritime transponder readings are point-in-time snapshots; the agent must never represent historical pings as continuous real-time positions.
- [ ] **Simulation Air-Gap Fallback**: When `HARNESS_NO_NETWORK=1` is enforced, telemetry queries must cleanly degrade to deterministic offline simulation without crashing.
- [ ] **Non-Destructive File Export**: 3D globe snapshots and orthomosaics must be written as discrete file artifacts in user-specified paths or temporary directories without modifying frontend UI bundles.

---

## Cross-Skill References

- [open-source-gis-architect](../open-source-gis-architect/SKILL.md) — Open source GIS engine selection and pipeline execution.
- [geospatial-disaster-simulation](../geospatial-disaster-simulation/SKILL.md) — Three.js building physics and disaster simulation.
- [differential-facet-verifier](../differential-facet-verifier/SKILL.md) — Multi-provider observation comparison.

