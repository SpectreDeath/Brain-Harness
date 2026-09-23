# Skill Summary Card: `open-source-gis-architect`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        open-source-gis-architect                │
│ Category:     data-engineering / geospatial            │
│ Invocation:   /open-source-gis-architect               │
│ Trigger:      "select gis software", "gis routing",    │
│               "spatial pipeline", "lidar processing",  │
│               "terrain analysis", "gis open source"    │
│ Version:      2.0.0                                    │
│ Requires:     "crafting-skills", "structured-data"     │
│ Provides:     "gis_architecture", "spatial_routing"    │
├────────────────────────────────────────────────────────┤
│ Target:       Architect, route, and validate spatial   │
│               workloads across 14 free GIS suites      │
│               using deterministic fitness heuristics.  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Spatial Architecture Loop

| Stage | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **1. Workload Interrogation** | Classify geometry, domain, formats, scale, and sector | `SpatialWorkloadProfile` | 6 dimensions populated; zero defense sector leakage |
| **2. Deterministic Routing** | Match features against 14-engine matrix | `EngineSelectionResult` | Primary + secondary engine selected (score ≥ 0.60) |
| **3. Pipeline DAG & CRS** | Decompose steps and enforce planar metric projection | `SpatialPipelineDAG` | Reprojection step inserted before all metric ops |
| **4. Headless Scripting** | Scaffold non-interactive runner scripts | Executable Python Runner | Exit code 0, zero input() calls, UTF-8 clean |
| **5. Visual Brief & Checkpoint** | Render HTML brief and verify geometry topology | `%TEMP%\gis-architect-*.html` | 0 critical topology errors, user approval received |

---

## Top Open-Source GIS Engine Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       GIS ENGINE SELECTION MATRIX                       │
├──────────────────────┬─────────┬────────────────────────────────────────┤
│ 1. Cartography & 3D  │ QGIS 3  │ ArcGIS Pro parity, PyQGIS plugins      │
├──────────────────────┼─────────┼────────────────────────────────────────┤
│ 2. Terrain & TWI     │ SAGA    │ Topographic Wetness Index, DEM morpho  │
├──────────────────────┼─────────┼────────────────────────────────────────┤
│ 3. LiDAR / LAS / LAZ │ Whitebox│ 410+ tools, LAS to shapefile, hydro-DEM│
├──────────────────────┼─────────┼────────────────────────────────────────┤
│ 4. Remote Sensing    │ GRASS   │ NASA/NOAA standard, 350+ raster tools  │
├──────────────────────┼─────────┼────────────────────────────────────────┤
│ 5. Spatial Stats     │ GeoDa   │ Moran's I, LISA clusters, regression   │
├──────────────────────┼─────────┼────────────────────────────────────────┤
│ 6. Field Survey GPS  │ gvSIG   │ gvSIG Mobile, OpenCAD geometry snapping│
└──────────────────────┴─────────┴────────────────────────────────────────┘
```

---

## Anti-Patterns Cheat Sheet

- **Esri Lock-In Reflex**: Reaching for expensive commercial licenses when open source delivers complete analytical parity.
- **On-The-Fly Projection Hazard**: Performing distance/buffer calculations in unprojected EPSG:4326 degrees.
- **Monolithic Engine Misalignment**: Crunching raw point clouds in a general GUI instead of Whitebox GAT.
- **Topology Sliver Ignorance**: Merging polygons without sliver threshold audits.
- **FalconView Civilian Recommendation**: Deploying combat flight planning tools in civilian workloads.
- **LiDAR Format Mismatch**: Loading massive LAS files into memory without surface grid interpolation.
- **Deprecated-Engine False Positive**: Relying on unmaintained prototypes for enterprise production pipelines.
- **Academic-Only Generalisation**: Misusing GeoDa for raster image processing or cartographic layouts.

---

## Invariants & Guardrails

- [ ] **CRS Metric Invariant**: Never execute buffer, area, or distance calculations on unprojected EPSG:4326 coordinates.
- [ ] **Defense Sector Firewall**: Workloads with sector=defense_restricted must halt immediately with FalconViewRestrictedDomainError.
- [ ] **LAS LiDAR Routing**: Point clouds (LAS/LAZ) must route to Whitebox GAT as primary engine; never desktop GUI alone.
- [ ] **Topology Integrity Gate**: Output layers must have zero critical topology defects (self-intersections, unclosed rings).
- [ ] **Script Hygiene Verification**: All generated scripts must pass AST walk inspection verifying zero input() calls.
- [ ] **Visual Brief Delivery**: Self-contained dark-theme HTML report rendered to %TEMP% before downstream processing.
- [ ] **Zero-Fork Config Precedence**: Operational budgets must resolve from 3-tier config hierarchy without hardcoded forks.

---

## Cross-Skill References

- [/book-to-skill-forge](../book-to-skill-forge/SKILL.md) — Literature deconstruction and pattern extraction.
- [/deep-skill-forge](../deep-skill-forge/SKILL.md) — Deep architectural synthesis and slotted domain models.
- [/structured-data-scout](../structured-data-scout/SKILL.md) — Sourcing structured spatial tabular data.
- [/epistemic-isnad-audit](../epistemic-isnad-audit/SKILL.md) — Chain-of-custody lineage for spatial decision heuristics.
