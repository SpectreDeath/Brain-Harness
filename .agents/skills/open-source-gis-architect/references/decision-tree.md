# Open-Source GIS Engine Routing Decision Tree

Authoritative deterministic routing heuristics extracted from GIS Geography comparative benchmark across 14 free GIS software suites.

```
                                  [Spatial Workload Input]
                                             │
                       Is sector == 'defense_restricted'?
                                      ┌──────┴──────┐
                                    YES             NO
                                     │              │
                       [HALT: FalconView]           │
                        Restricted Domain           │
                                                    ▼
                                          What is primary domain?
                                                    │
        ┌──────────────┬──────────────┬─────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼             ▼              ▼              ▼
     [LiDAR /       [Terrain /     [Spatial     [Remote        [Cartography /  [Field Survey /
    Hydrology]     Morphometry]   Statistics]   Sensing]         3D Maps]        Mobile GPS]
        │              │              │             │              │              │
  Whitebox GAT      SAGA GIS        GeoDa       GRASS GIS        QGIS 3       gvSIG Mobile
 (Sec: SAGA GIS) (Sec: GRASS)  (Sec: GRASS)   (Sec: ILWIS)    (Sec: gvSIG)    (Sec: Birdi)
```

---

## The 13 Deterministic Routing Paths

### Path 1: `lidar_hydrology_whitebox_gat`
- **Trigger**: `domain == 'lidar_hydrology' OR 'LAS' in formats OR 'LAZ' in formats OR has_lidar == True`
- **Primary Engine**: **Whitebox GAT** (4.8 rating on LiDAR). Succeeded Terrain Analysis System (TAS). 410+ tools. LAS-to-shapefile native pipeline.
- **Secondary Engine**: **SAGA GIS** (for raster DEM interpolation and gap filling).

### Path 2: `terrain_morphometry_saga_gis`
- **Trigger**: `domain in ('terrain_morphometry', 'dem_derivatives') OR 'twi' in analysis`
- **Primary Engine**: **SAGA GIS** (3.1 stars). Definitive suite for Topographic Wetness Index (TWI) and Topographic Position Classification.
- **Secondary Engine**: **GRASS GIS** (digital terrain manipulation, `r.slope.aspect`, `r.relief`).

### Path 3: `spatial_statistics_geoda`
- **Trigger**: `needs_statistics == True OR domain == 'spatial_statistics' OR analysis in ('moran_i', 'lisa', 'spatial_regression')`
- **Primary Engine**: **GeoDa** (3.0 stars). Academic spatial statistics gateway (Harvard, MIT, Cornell). Fast LISA clustering and spatial OLS/lag/error regressions.
- **Secondary Engine**: **GRASS GIS** (`v.kernel`, `r.stats`).

### Path 4: `remote_sensing_grass_gis`
- **Trigger**: `domain in ('remote_sensing', 'image_processing') OR analysis == 'spectral_classification'`
- **Primary Engine**: **GRASS GIS** (3.9 stars). NASA, NOAA, USDA, USGS benchmark. 350+ rock-solid tools, multispectral band clustering (`i.cluster`).
- **Secondary Engine**: **ILWIS** (spectral band manipulation and time-series animation).

### Path 5: `cartography_qgis3`
- **Trigger**: `domain in ('cartography', '3d_visualization', 'general_gis') OR output_type == 'executive_map'`
- **Primary Engine**: **QGIS 3** (4.8 stars). Full ArcGIS Pro parity, 3D cartographic renderer, print layout engine, PyQGIS ecosystem.
- **Secondary Engine**: **gvSIG** (OpenCAD precision editing).

### Path 6: `field_survey_gvsig_mobile`
- **Trigger**: `domain in ('field_survey', 'mobile_gps') OR needs_mobile == True OR output_type == 'mobile_gps'`
- **Primary Engine**: **gvSIG** (3.6 stars). gvSIG Mobile for GPS field capture, OpenCAD snapping and vertex editing, NavTable vertical record inspection.
- **Secondary Engine**: **Birdi** (freemium cloud inspection platform for drone inspections and severity tracking).

### Path 7: `watershed_delineation_mapwindow`
- **Trigger**: `domain == 'watershed_delineation' OR sector == 'epa_basins'`
- **Primary Engine**: **MapWindow 5** (2.6 stars). Born from US EPA 'Basins' contract. TauDEM automated watershed delineation and HydroDesktop.
- **Secondary Engine**: **Whitebox GAT** (hydro-geomorphic routing).

### Path 8: `biodiversity_diva_gis`
- **Trigger**: `domain in ('biodiversity', 'species_distribution') OR analysis == 'dna_distribution'`
- **Primary Engine**: **Diva GIS** (1.5 stars). Specialized biological richness and DNA marker mapping with WorldClim climate extractions.
- **Secondary Engine**: **GeoDa** (spatial clustering of observations).

### Path 9: `urban_acoustics_orbisgis`
- **Trigger**: `domain in ('urban_acoustics', 'noise_mapping')`
- **Primary Engine**: **OrbisGIS** (1.9 stars). Research engine with built-in noise map algorithms and H2GIS spatial SQL.
- **Secondary Engine**: **QGIS 3** (cartographic rendering of output acoustic grids).

### Path 10: `ogc_services_udig`
- **Trigger**: `domain == 'ogc_web_services' OR 'WMS' in formats OR 'WFS' in formats OR 'WPS' in formats`
- **Primary Engine**: **uDig** (2.5 stars). User-friendly Desktop Internet GIS with Mapnik integration and standards-compliant OGC consumption.
- **Secondary Engine**: **OpenJUMP** (web processing plugins).

### Path 11: `vector_conflation_openjump`
- **Trigger**: `domain in ('vector_conflation', 'large_vector_overlay')`
- **Primary Engine**: **OpenJUMP** (2.4 stars). JAVA Unified Mapping Platform with conflation algorithms and high-capacity vector rendering.
- **Secondary Engine**: **QGIS 3** (topology cleaning tools).

### Path 12: `land_water_management_ilwis`
- **Trigger**: `domain in ('land_water_management', 'time_series_raster') OR has_time_series == True`
- **Primary Engine**: **ILWIS** (3.2 stars). Integrated Land and Water Information Management with temporal animation and spectral bands.
- **Secondary Engine**: **GRASS GIS** (temporal raster modules `t.rast.*`).

### Path 13: `defense_restricted_halt`
- **Trigger**: `sector == 'defense_restricted'`
- **Action**: **HALT IMMEDIATELY.** Emit `FalconViewRestrictedDomainError`. Consult `references/restricted-domain-notes.md` for informational context only.
