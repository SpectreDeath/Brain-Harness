# How-To Guides: Earth Engine Plugin Recipes

Practical, problem-oriented recipes for common geospatial intelligence workflows.

---

## Recipe 1: Cloud-Free Temporal Composite Generation

Produce a cloud-masked seasonal median composite from Sentinel-2 image collections:

```python
from plugins.geospatial_and_osint.earth_engine_imagery.main import ee_composite_timeseries

composite = ee_composite_timeseries(
    collection_id="COPERNICUS/S2_SR_HARMONIZED",
    bbox=[-122.5, 37.7, -122.2, 37.9],  # San Francisco Bay Area
    start_date="2026-06-01",
    end_date="2026-08-31",
    composite_method="median",
    mask_clouds=True,
)

print(f"Composite status: {composite['status']}")
print(f"Method: {composite['composite_method']}")
print(f"Cloud masking applied: {composite['mask_clouds_applied']}")
```

---

## Recipe 2: Slope & Aspect Analysis from 3DEP Topographic DEMs

Evaluate terrain slope, aspect, and hillshade for environmental risk or watershed runoff modeling:

```python
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import ee_analyze_terrain

terrain = ee_analyze_terrain(
    dem_asset="USGS/3DEP/10m",
    bbox=[-122.5, 37.7, -122.3, 37.9],
    compute_slope=True,
    compute_aspect=True,
    compute_hillshade=True,
)

metrics = terrain["terrain_metrics"]
print(f"Mean Elevation: {metrics['elevation_mean_meters']} m")
print(f"Mean Slope: {metrics['slope_mean_degrees']} deg")
print(f"Dominant Aspect: {metrics['dominant_aspect_degrees']} ({metrics['aspect_cardinal']})")
print(f"Shaded Relief Illumination: {metrics['hillshade_mean_illumination']} / 255")
```

---

## Recipe 3: Querying Vector Boundaries & Spatial Intersections

Retrieve administrative or hydrological boundaries intersecting a region of interest:

```python
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import ee_vector_spatial_query

boundaries = ee_vector_spatial_query(
    table_asset="TIGER/2018/States",
    filter_property="NAME",
    filter_value="California",
    limit=5,
)

for feature in boundaries["features"]:
    props = feature["properties"]
    print(f"Region: {props.get('NAME')}, Area: {props.get('AREA_SQKM')} sq km")
```

---

## Recipe 4: Discovering Environmental Datasets in the Data Catalog

Search the global Earth Engine catalog for precipitation and climate reanalysis products:

```python
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import ee_query_data_catalog

catalog = ee_query_data_catalog(
    query="precipitation",
    category="climate",
    limit=5,
)

for ds in catalog["datasets"]:
    print(f"[{ds['id']}] {ds['title']}")
    print(f"  Resolution: {ds['spatial_resolution_meters']} m | Start: {ds['time_start']}")
```

---

## Recipe 5: Monitoring Batch Export Tasks

Check background asynchronous export and import task statuses:

```python
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import ee_manage_batch_task

# List active and recent tasks
task_list = ee_manage_batch_task(action="list", limit=10)
for t in task_list["tasks"]:
    print(f"Task ID: {t['id']}, State: {t['state']}, Progress: {t['progress']}%")

# Inspect individual task detail
task_detail = ee_manage_batch_task(action="status", task_id="task_ee_export_20260908_001")
print(f"Destination: {task_detail.get('destination')}")
```
