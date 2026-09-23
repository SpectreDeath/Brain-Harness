# Open-Source GIS Format Compatibility Matrix

This matrix maps spatial file formats and protocols to optimal open-source processing engines and their recommended intermediate formats.

| Format / Protocol | Category | Primary Engine | Secondary Engine | Recommended Intermediate Format | Invariant Warning |
|---|---|---|---|---|---|
| **LAS / LAZ** | LiDAR Point Cloud | **Whitebox GAT** | QGIS 3 (via PDAL) | GeoTIFF (DEM) / Shapefile / GeoPackage | Never load raw LAS > 50M pts into desktop GUI memory. Convert to DEM or slice with Whitebox. |
| **GeoTIFF / COG** | Raster Ortho / DEM | **QGIS 3 / GRASS** | SAGA GIS | Cloud-Optimized GeoTIFF (COG) | Maintain NoData value mask during reclassification to prevent border artifacts. |
| **SAGA Grid (.sgrd)** | Geoscientific Raster | **SAGA GIS** | QGIS 3 (via GDAL) | GeoTIFF | SAGA formats should be exported to GeoTIFF before pipeline handoff. |
| **Shapefile (.shp)** | Legacy Vector | **QGIS 3 / gvSIG** | OpenJUMP | GeoPackage (.gpkg) | 2GB file limit and 10-char column truncation hazard. Convert to GeoPackage immediately. |
| **GeoPackage (.gpkg)** | Standard Vector/Raster | **QGIS 3** | GeoDa | SQLite / GeoPackage | Preferred default vector format across all open-source pipelines. |
| **WMS / WFS / WPS** | OGC Web Services | **uDig** | QGIS 3 | Local Cache (GeoPackage) | Always verify projection alignment between client viewport and WMS layer. |
| **CAD (DWG / DXF)** | Computer-Aided Design | **gvSIG** | QGIS 3 | GeoPackage | Use OpenCAD tools in gvSIG for precision vertex snapping and geometry cleanup. |
| **WorldClim Grid** | Bioclimatic Raster | **Diva GIS** | SAGA GIS | GeoTIFF | Extract point observations against bioclim grids before downstream spatial stats. |
| **KMZ / MrSID / MXD** | Tactical / Legacy Esri | **FalconView** | QGIS 3 | GeoPackage / GeoTIFF | FalconView is defense-restricted; for civilian workflows, convert MXD via QGIS bridge. |
| **CSV / Tabular** | Attribute Coordinates | **GeoDa** | QGIS 3 | GeoPackage | Geocode coordinates to EPSG:4326, then reproject to UTM before distance calculations. |
