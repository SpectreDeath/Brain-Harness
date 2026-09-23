# Spatial Workload Diagnostic Decision Tree

8-question diagnostic interview to classify spatial workloads across 6 foundational dimensions:

## The 8 Diagnostic Questions

1. **What is the primary spatial geometry type?**
   - Options: `point_cloud` | `raster_dem` | `satellite_multispectral` | `vector_polygon` | `tabular_coordinates`
   - If `point_cloud` → Route directly to Whitebox GAT evaluation.

2. **What analytical operation is required?**
   - Options: `lidar_filtering` | `terrain_morphometry` (TWI/TPC) | `spatial_regression` (Moran's I/LISA) | `spectral_classification` | `watershed_delineation` | `conflation` | `cartography`
   - Guides engine matching across specialized algorithms.

3. **What is the sector and institutional context?**
   - Options: `civilian` | `academic` | `government_science` | `defense_restricted`
   - If `defense_restricted` → Trigger immediate HALT (`FalconViewRestrictedDomainError`).

4. **What are the incoming data formats?**
   - Options: `LAS/LAZ` | `GeoTIFF` | `Shapefile` | `GeoPackage` | `WMS/WFS` | `CAD (DWG/DXF)` | `WorldClim`
   - Checked against format compatibility matrix.

5. **Is field GPS data collection or mobile inspection required?**
   - Options: `yes_gps_survey` → gvSIG Mobile | `yes_drone_inspection` → Birdi | `no_desktop_only`

6. **Are temporal raster time series involved?**
   - Options: `yes_time_series` → ILWIS / GRASS | `no_static_layers`

7. **What is the required deliverable format?**
   - Options: `executive_cartographic_map` (QGIS 3) | `headless_batch_pipeline` (Python/GDAL/Whitebox) | `statistical_report` (GeoDa) | `3d_web_service` (QGIS Server)

8. **What is the data volume?**
   - Options: `< 1 GB` | `1 – 50 GB` | `> 50 GB`
   - Determines out-of-core streaming and memory budget enforcement.
