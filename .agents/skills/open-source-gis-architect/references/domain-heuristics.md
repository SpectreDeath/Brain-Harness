# Domain Heuristics & Epistemic Mental Models

Heuristics distilled from GIS Geography comparative literature across 14 engines:

## 1. The Star-to-Domain Heuristic
- **≥ 3.5 Stars (QGIS 3, GRASS GIS, Whitebox GAT, Birdi, gvSIG)**: Production-grade for mission-critical pipelines, high stability, broad community support.
- **2.0 – 3.5 Stars (ILWIS, SAGA GIS, GeoDa, MapWindow, uDig, OpenJUMP)**: Specialized powerhouse tools. Outstanding in their specific analytical niche (e.g. SAGA for terrain, GeoDa for spatial autocorrelation), but weaker as general-purpose desktop editors.
- **< 2.0 Stars (FalconView, OrbisGIS, Diva GIS)**: Niche domain software. FalconView is defense-restricted; OrbisGIS is academic research under active development; Diva GIS is legacy biological research.

## 2. The Government Trust Ladder
- Endorsement by US federal scientific bodies (**NASA, NOAA, USDA, USGS**) for **GRASS GIS** is the strongest reliability signal in the open-source GIS catalog.
- When auditability, topological rigor (`v.clean`), and rock-solid raster calculations (`r.mapcalc`) are required by public sector projects, GRASS GIS is the primary analytical backend.

## 3. The LiDAR Routing Invariant
- **LAS / LAZ point cloud data mandates Whitebox GAT** as the primary engine.
- Whitebox GAT evolved from TAS (Terrain Analysis System) with 410+ tools specifically tuned for hydro-geomorphic DEM conditioning and point cloud classification (LAS-to-shapefile).
- Standard desktop GIS (QGIS, gvSIG) without specialized plugins will bog down or crash on raw multi-gigabyte point clouds.

## 4. The DEM Agnosticism Rule
- *"If you have a DEM and don't know what to do with it — you NEED to look at SAGA GIS."* (Direct quote from source literature).
- SAGA GIS provides the deepest catalog of out-of-the-box geomorphometric algorithms:
  - **Topographic Wetness Index (TWI)**: Predicts hydrological accumulation and soil moisture.
  - **Topographic Position Classification (TPC)**: Segment slopes into crests, valleys, and mid-slopes.
  - **Raster Gap Filling**: Cleans artifacts and interpolates missing elevation data seamlessly.

## 5. The Defense Firewall Pattern
- FalconView was designed by Georgia Tech for the US Department of Defense and National Geospatial-Intelligence Agencies for combat flight planning.
- Capabilities include SkyView fly-through, MIL-STD symbology, and tactical reconnaissance displays.
- **Safety Boundary**: Must never be recommended or deployed in civilian, commercial, or public-health spatial pipelines. Structure as an informational reference only, guarded by `FalconViewRestrictedDomainError`.
