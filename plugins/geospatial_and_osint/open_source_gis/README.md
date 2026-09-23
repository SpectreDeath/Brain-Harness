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
