# Offline Critical Infrastructure Multi-Source Spatial Indexing Engine

## Architectural Thesis
Critical Infrastructure queries (identifying subsea fiber cables, hyperscale cloud regions, hydroelectric dams, and military radar installations within a tactical corridor) require instantaneous $O(1)$ spatial queries that cannot depend on high-latency third-party external APIs.

## Multi-Source Dataset Topology
The target repository bundles 7MB of high-fidelity pre-indexed offline GIS assets:
- `telegeography_submarine_cables/landing-point-geo.json`: 350KB GeoJSON of subsea cable terminations.
- `telegeography_submarine_cables/cable-geo.json`: 711KB GeoJSON representing worldwide subsea optical fiber routes.
- `datacenters/datacenters.geojsonl`: 2.5MB GeoJSONL detailing hyperscale datacenters, cloud campuses, and power capacities.
- `dams/dams.geojsonl`: 713KB GeoJSONL detailing major civil and hydroelectric dams.
- `osm_military_names/names.json`: 3.7MB OpenStreetMap military installation names and boundary classifications.

## Provenance & Isnad Lineage
- Dataset Root: `D:\GitHub\cloned\gods-eye-view\src\data\local_data\`
- Attribution Manifest: `D:\GitHub\cloned\gods-eye-view\DATA_SOURCES.md`
- Harness Slotted Implementation: `plugins\geospatial_and_osint\gods_eye_view\infrastructure_store.py`
