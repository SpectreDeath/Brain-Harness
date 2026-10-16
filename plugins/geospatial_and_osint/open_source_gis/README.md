# Open-Source GIS Architect Plugin (`plugin.open_source_gis`)

Provides deterministic analytical fitness matching across 14 free and open-source GIS software suites, strict CRS planar projection safety verification, geometric topology auditing, and automated Stage 5 HTML visual briefs.

## Architecture & Seams

- **Service Key**: `OPEN_SOURCE_GIS_SERVICE_KEY`
- **Protocol**: `OpenSourceGisService` in `src/harness/services/open_source_gis.py`
- **Category**: `geospatial_and_osint`
- **Isolation**: `subprocess` (trusted in-process capable)

## Exposed Tools

1. `gis_route_workload`: Matches workload profiles (geometry, domain, formats, scale, sector) to optimal primary and secondary GIS engines.
2. `gis_validate_pipeline`: Verifies pipeline execution DAGs for metric CRS projection safety (`EPSG:4326` forbidden before metric ops).
3. `gis_audit_topology`: Audits polygon geometry rings for self-intersections, unclosed rings, duplicate vertices, and micro-slivers.
4. `gis_architect_workload`: Composite end-to-end workload architecture interrogation emitting structured receipts and Stage 5 HTML visual briefs.

## Operational Budgets (Zero-Fork)

Default budgets and weights are configured in `config.default.yaml` with 3-tier precedence:
1. Workspace root `.agents/skills.config.yaml`
2. Co-located `config.default.yaml`
3. In-memory hardcoded fallback


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `gis_route_workload` | `(domain, geometry_type, data_formats, sector, analysis, has_lidar, needs_statistics, needs_mobile)` | Route spatial analysis workloads to optimal open-source GIS engines (QGIS, SAGA, Whitebox, GRASS, GeoDa, gvSIG, MapWindow, Diva GIS, OrbisGIS) using deterministic fitness matching |
| `gis_validate_pipeline` | `(steps)` | Validate a spatial pipeline execution DAG for metric Coordinate Reference System (CRS) projection safety and format handoffs |
| `gis_audit_topology` | `(features, sliver_threshold_m2)` | Audit vector polygon geometries for topological integrity: self-intersections, unclosed rings, duplicate vertices, and micro-slivers |
| `gis_architect_workload` | `(workload_profile, pipeline_steps, features, generate_brief)` | End-to-end spatial workload architecture interrogation: routes engines, checks DAG CRS safety, audits geometry topology, and renders Stage 5 HTML visual brief |
