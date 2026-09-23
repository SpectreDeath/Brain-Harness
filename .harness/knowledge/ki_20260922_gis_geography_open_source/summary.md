# Open-Source GIS Architecture & Multicriteria Software Benchmarking

## Executive Summary

This Knowledge Item synthesizes the architectural heuristics, empirical benchmarks, and operational trade-offs across 14 leading free and open-source Geographic Information Systems (GIS), distilled from primary literature (*"13 Free GIS Software Options: Map the World in Open Source"*, GIS Geography, 2025). It bridges literature deconstruction into autonomous agent routing capabilities, establishing deterministic fitness criteria to prevent monolithic desktop misalignments and costly commercial lock-in.

---

## Epistemic Mental Models & Architectural Heuristics

### 1. The Star-to-Domain Production Heuristic
- **≥ 3.5 Stars (QGIS 3, GRASS GIS, Whitebox GAT, Birdi, gvSIG)**: Production-grade for enterprise automation pipelines, headless batch processing, and stable cross-platform execution.
- **2.0 – 3.5 Stars (ILWIS, SAGA GIS, GeoDa, MapWindow 5, uDig, OpenJUMP)**: Specialized powerhouse engines. Superlative in targeted niches (e.g. SAGA for geomorphometry, GeoDa for spatial autocorrelation), but narrower in generalized cartographic layout.
- **< 2.0 Stars (FalconView, OrbisGIS, Diva GIS)**: Niche domain software requiring strict operational constraints. FalconView is defense-restricted; OrbisGIS is academic research under active development; Diva GIS is legacy biological research.

### 2. The Government Trust Ladder
- Federal scientific agency endorsement (**NASA, NOAA, USDA, USGS**) establishes **GRASS GIS** as the primary open-source standard for high-assurance raster calculation (`r.mapcalc`), image classification (`i.cluster`), and topological vector cleaning (`v.clean`).
- In public-sector environmental and land management pipelines, GRASS GIS provides mathematically verifiable algorithms with over 350 native modules.

### 3. The LiDAR Routing Invariant
- **LAS / LAZ point cloud inputs mandate Whitebox GAT as primary engine.**
- Succeeded the Terrain Analysis System (TAS) with 410+ tools fine-tuned for hydro-geomorphic applications.
- Provides native LAS-to-shapefile extraction and bare-earth DEM conditioning, bypassing the memory-exhaustion failure modes common to general desktop viewers attempting to render raw multi-million vertex point clouds.

### 4. The DEM Agnosticism Rule
- *"If you have a DEM and don't know what to do with it — you NEED to look at SAGA GIS."*
- SAGA GIS provides the deepest catalog of out-of-the-box geomorphometric algorithms:
  - **Topographic Wetness Index (TWI)**: Predicts hydrological accumulation and soil moisture.
  - **Topographic Position Classification (TPC)**: Segments terrain into crests, valley bottoms, and mid-slopes.
  - **Raster Gap Filling**: Cleans elevation voids and artifacts seamlessly.

### 5. The Defense Firewall Pattern
- FalconView was developed by Georgia Tech Research Institute for the US Department of Defense (DoD) and National Geospatial-Intelligence Agencies for combat flight planning.
- Features include SkyView 3D fly-through, MIL-STD symbology, and tactical overlay rendering.
- **Safety Rule**: FalconView must never be recommended or configured in civilian, commercial, municipal, or academic pipelines. In autonomous agent loops, workloads with `sector == "defense_restricted"` must raise `FalconViewRestrictedDomainError` and halt immediately.

---

## Comparative Catalog Summary

| Engine | Rating | Primary Strength | Flagship Specialized Module | License |
|---|---|---|---|---|
| **QGIS 3** | 4.8 ★ | ArcGIS Pro Parity, 3D Maps | PyQGIS, Processing Toolbox | GPL-2.0 |
| **GRASS GIS** | 3.9 ★ | Government Land Management | `r.watershed`, `v.clean`, `i.cluster` | GPL-2.0 |
| **Whitebox GAT** | 3.8 ★ | LiDAR & Hydro-Geomorphic DEM | WhiteboxTools, LAS to Shapefile | GPL-3.0 |
| **Birdi** | 3.6 ★ | Drone & Asset Inspection | Severity Tracking, Cloud Drone Platform | Freemium |
| **gvSIG** | 3.6 ★ | Field GPS & OpenCAD Editing | gvSIG Mobile, NavTable, OpenCAD | GPL-2.0 |
| **ILWIS** | 3.2 ★ | Integrated Land & Water | Time Series Raster, Spectral Bands | GPL-2.0 |
| **SAGA GIS** | 3.1 ★ | Geoscientific Terrain Morphometry | Topographic Wetness Index, Gap Filling | GPL-2.0 |
| **GeoDa** | 3.0 ★ | Spatial Econometrics & Autocorrelation | Moran's I, LISA Clusters, Spatial Lag | GPL-2.0 |
| **MapWindow 5** | 2.6 ★ | EPA Basins Watershed Modeling | TauDEM Automatic Delineation | MPL-1.1 |
| **uDig** | 2.5 ★ | OGC Internet Web Standards | WMS/WFS/WPS Client, Mapnik Rendering | LGPL-2.1 |
| **OpenJUMP** | 2.4 ★ | Heavy Vector Conflation | Conflation Plugins, Choropleth Plotting | GPL-2.0 |
| **FalconView** | 2.1 ★ | Combat Flight Navigation | SkyView, MIL-STD (DEFENSE RESTRICTED) | Mixed |
| **OrbisGIS** | 1.9 ★ | Urban Acoustics Research | Noise Map Engine, H2GIS Spatial SQL | GPL-3.0 |
| **Diva GIS** | 1.5 ★ | Biodiversity & DNA Mapping | WorldClim Bioclimatic Extractions | Freeware |

---

## Verifiable Isnad Lineage

- **Grounding Source**: GIS Geography, *"13 Free GIS Software Options: Map the World in Open Source"*, last updated 2025-08-03.
- **Cognitive Distillation Seams**:
  1. Epistemic Introspection: `.harness/knowledge/ki_20260922_gis_geography_open_source/` (Decision ID `dec_20260922_gis_01`).
  2. Procedural Skill Package: `.agents/skills/open-source-gis-architect/` (SKILL.md, CARD.md, scripts/engine.py).
- **Governing Agent Standards**: `AGENTS.md` Rule 11 (Hygiene & Boundaries), Rule 12 (Slotted & Frozen Dataclasses), Rule 37 (ASCII Card Formatting), Rule 40 (Dual-File Directory Invariant), Rule 41 (Dual-Lens Distillation Seam), Rule 43 (Frozen Dataclass Mutation Assertion), Rule 44 (Dual-Tier Catalog Budget).
