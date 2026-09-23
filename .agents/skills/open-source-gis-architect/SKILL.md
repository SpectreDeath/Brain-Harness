---
name: open-source-gis-architect
description: Select, route, and validate open-source GIS engine workloads across 14 engines using deterministic decision trees, CRS safety gates, LiDAR format routing, and defense-restricted domain isolation. Do not use for commercial Esri license procurement, raw satellite imagery downloading, or defense flight planning.
---

# Open-Source GIS Architect Engine

The `open-source-gis-architect` engine synthesizes literature-grounded geospatial intelligence across 14 free and open-source GIS software suites. It replaces monolithic tool assumptions with deterministic analytical fitness matching, rigid CRS safety verification, and automated topological hygiene checks.

Every spatial analysis lifecycle follows a sequential five-stage progression:

```
[1. Workload Interrogation] → [2. Engine Routing] → [3. Pipeline DAG & CRS] → [4. Headless Scripting] → [5. Visual Brief & Checkpoint]
```

See [CARD.md](CARD.md) for the fast-lookup cheat sheet, blocking invariants, and engine scorecards.
Consult `/book-to-skill-forge`, `/deep-skill-forge`, and `/structured-data-scout` for architectural integration.
Detailed heuristics and matrices are partitioned in `references/` for progressive disclosure:
- Deterministic Decision Tree: [references/decision-tree.md](references/decision-tree.md)
- Format Compatibility Matrix: [references/format-compatibility.md](references/format-compatibility.md)
- Epistemic Domain Heuristics: [references/domain-heuristics.md](references/domain-heuristics.md)
- Restricted Domain Notes: [references/restricted-domain-notes.md](references/restricted-domain-notes.md)

---

## 1. Workload Interrogation & Domain Classification

Classify the incoming spatial analysis workload across 6 foundational dimensions:
1. **Spatial Geometry Type**: Determine if the primary data structure is a vector polygon layer, digital elevation model (DEM), LiDAR point cloud (LAS/LAZ), satellite multispectral raster, or coordinate table.
2. **Analytical Operation**: Pinpoint the computational objective (e.g. LiDAR bare-earth filtering, DEM Topographic Wetness Index calculation, spatial autocorrelation regression, multispectral clustering, or CAD snapping).
3. **Institutional Sector**: Identify whether the workload is civilian, academic, environmental, public health, or defense/military.
   - **Critical Boundary**: If `sector == "defense_restricted"`, halt immediately with `FalconViewRestrictedDomainError`. Never recommend FalconView to civilian operators.
4. **Data Formats**: Catalogue source files against `references/format-compatibility.md`.
5. **Collection Mode**: Check if field mobile GPS (gvSIG Mobile) or drone inspection (Birdi) is required.
6. **Data Volume & Scale**: Assess whether dataset fits in memory or requires chunked streaming.

> **Completion criterion**: SpatialWorkloadProfile initialized with all 6 dimensions populated; zero defense sector leakage confirmed.

---

## 2. Deterministic Engine Routing

Execute the deterministic routing catalog (`GISEngineCatalog.route_workload`) matching workload features against the 14-engine catalog:

1. **LiDAR & Point Clouds**: Route all LAS/LAZ workloads directly to **Whitebox GAT** (successor to TAS, 410+ tools, native LAS-to-shapefile). Set SAGA GIS as secondary.
2. **DEM Morphometry**: Route Topographic Wetness Index (TWI) and landform classification to **SAGA GIS**. Set GRASS GIS as secondary.
3. **Spatial Statistics & Econometrics**: Route Moran's I, LISA clusters, and spatial lag/error models to **GeoDa**. Set GRASS GIS as secondary.
4. **Remote Sensing & Multispectral**: Route satellite image processing to **GRASS GIS** (NASA/NOAA trust standard, 350+ tools). Set ILWIS as secondary.
5. **Mobile Field Capture**: Route GPS surveying to **gvSIG Mobile** with OpenCAD editing.
6. **Watershed Modeling**: Route EPA Basins or hydrological delineation to **MapWindow 5** (TauDEM integration).
7. **Biodiversity & Climate**: Route DNA marker distribution and species richness to **Diva GIS** (WorldClim extraction).
8. **Cartography & Production**: Route general GIS and 3D visualization to **QGIS 3** (full ArcGIS Pro parity).

> **Completion criterion**: EngineSelectionResult emitted with primary engine, secondary engine, composite fitness score ≥ 0.60, and named routing path.

---

## 3. Spatial Pipeline DAG Construction & CRS Safety

Decompose the spatial workflow into an acyclic execution graph (`SpatialPipelineDAG`) enforcing strict Coordinate Reference System (CRS) invariants:

1. **CRS Metric Invariant**: Never execute metric spatial operations (`buffer`, `area`, `distance`, `density`, `watershed_delineation`, `slope_aspect`) on unprojected geographic coordinates (`EPSG:4326` / WGS84).
2. **Conformal Reprojection**: Inject an explicit reprojection step converting vector or raster layers into the appropriate local UTM zone or conformal projected CRS before metric operations.
3. **Intermediate Serialization**: Mandate GeoPackage (`.gpkg`) for vector exchanges and Cloud-Optimized GeoTIFF (`.tif`) for raster exchanges between pipeline nodes. Avoid raw shapefiles.

> **Completion criterion**: SpatialPipelineDAG validated with zero CRS projection violations and clean format handoffs.

---

## 4. Headless Script Execution & Subprocess Sandboxing

Scaffold and execute non-interactive Python runner scripts conforming to platform standards:

1. **PEP 723 Metadata**: Declare script dependencies explicitly at module head.
2. **UTF-8 Standard Streams**: Enforce `sys.stdout.reconfigure(encoding='utf-8')` to prevent Windows `cp1252` encoding failures.
3. **Zero Interactive Prompts**: Forbid all `input()` calls; inject parameters via command-line arguments (`--workload-json`).
4. **Subprocess Pipe Disposal**: Drain and close stdin, stdout, and stderr file descriptors inside `finally` blocks.

> **Completion criterion**: Subprocess scripts execute to completion with exit code 0; zero interactive input() calls verified by AST walk.

---

## 5. Visual Spatial Brief & Verification Checkpoint

Deliver architectural transparency and quality assurance through an interactive report and a mandatory checkpoint gate:

### Visual Brief Specification (%TEMP%)
1. Generate an interactive, self-contained HTML visual brief written to `%TEMP%\gis-architect-<timestamp>.html`.
2. Theme: Clean dark theme (`#0d1117`) with Tailwind CSS and Mermaid.js via CDN.
3. Contents:
   - Visual Mermaid DAG displaying data inputs, CRS transformations, engine processing steps, and output files.
   - Comprehensive benchmark table highlighting selected engine vs alternates across star rating, license, and tools.
   - Geometry topology audit card summarizing sliver count, self-intersections, and vertex health.

### Mandatory Checkpoint Gate (RequestFeedback)
1. Execute `TopologyAuditReport` on all output vector layers.
2. Assert zero `CRITICAL` topological defects (self-intersections, unclosed rings).
3. Emit a structured markdown receipt:
   ```markdown
   ### [Spatial Architecture Receipt]
   - **Primary Engine**: `Whitebox GAT` (Fitness: 0.96)
   - **Routing Path**: `lidar_hydrology_whitebox_gat`
   - **CRS Transformation**: `EPSG:4326` → `EPSG:32632 (UTM Zone 32N)`
   - **Topology Health**: [PASSED] 0 self-intersections, 0 sliver polygons
   - **Visual Brief**: file:///C:/Users/.../AppData/Local/Temp/gis-architect-*.html
   ```
4. Pause for user sign-off (`RequestFeedback: true`) prior to long-running raster crunching or batch cloud execution.

> **Completion criterion**: Self-contained HTML Visual Brief rendered to %TEMP%; topology audit passed with zero critical defects; user sign-off checkpoint emitted.

---

## Anti-Patterns

- **Esri Lock-In Reflex** — Defaulting to expensive commercial proprietary licenses when mature open-source tools (QGIS 3, GRASS, SAGA) provide complete feature parity.
- **On-The-Fly Projection Hazard** — Executing planar metric calculations (buffers, areas, distances) on unprojected geographic degrees (`EPSG:4326`), producing catastrophic spherical distortion.
- **Monolithic Engine Misalignment** — Forcing high-density raw LiDAR point clouds into a standard desktop GUI rather than routing to specialized engines like Whitebox GAT.
- **Topology Sliver Ignorance** — Generating uncleaned polygon overlays without checking for micro-slivers below the operational area threshold.
- **FalconView Civilian Recommendation** — Recommending defense-restricted combat flight planning tools for standard municipal, agricultural, or environmental mapping projects.
- **LiDAR Format Mismatch** — Attempting to open raw multi-gigabyte LAS/LAZ files in unsupported tools without building a raster DEM bare-earth surface first.
- **Deprecated-Engine False Positive** — Selecting research-prototype or unmaintained software for high-availability enterprise automation pipelines.
- **Academic-Only Generalisation** — Deploying specialized statistical packages like GeoDa for general raster cartography or field GPS capture.
