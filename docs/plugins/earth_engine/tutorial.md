# Tutorial: Planetary Earth Observation with Earth Engine Plugins

This tutorial guides you from zero to executing your first planetary satellite imagery analysis workflow in Brain Harness using the partitioned Earth Engine plugins.

## Learning Objectives

By the end of this tutorial, you will:
1. Understand how Earth Engine is mounted into the Brain Harness IoC container.
2. Search and discover Sentinel-2 multispectral scenes over a region of interest.
3. Compute a Normalized Difference Vegetation Index (NDVI) layer.
4. Extract zonal vegetation statistics over a designated agricultural polygon.
5. Generate a visual preview thumbnail URL for agentic inspection.

---

## Prerequisites

- Python &ge; 3.10
- Brain Harness with `plugins/geospatial_and_osint/earth_engine_imagery` and `plugins/geospatial_and_osint/earth_engine_spatial_analytics` enabled.
- *(Optional for live mode)* Google Cloud project configured with Earth Engine API enabled.

---

## Step 1: Discovering Satellite Scenes

We begin by searching for low-cloud Sentinel-2 surface reflectance scenes over an agricultural area (e.g. California Central Valley):

```python
from plugins.geospatial_and_osint.earth_engine_imagery.main import ee_search_image_collection

# Define bounding box [min_lon, min_lat, max_lon, max_lat]
bbox = [-120.6, 36.4, -120.3, 36.7]

result = ee_search_image_collection(
    collection_id="COPERNICUS/S2_SR_HARMONIZED",
    bbox=bbox,
    start_date="2026-05-01",
    end_date="2026-06-01",
    max_cloud_cover=15.0,
    limit=5,
)

print(f"Scenes found: {result['total_found']}")
for scene in result["scenes"]:
    print(f"Scene: {scene['id']}, Cloud: {scene.get('cloud_cover_percentage', 0.0)}%")
```

---

## Step 2: Calculating Vegetation Health (NDVI)

Select a candidate scene ID from the search results and compute the Normalized Difference Vegetation Index (NDVI) using near-infrared (Band 8) and red (Band 4):

```python
from plugins.geospatial_and_osint.earth_engine_imagery.main import ee_compute_spectral_index

scene_id = result["scenes"][0]["id"]

ndvi_result = ee_compute_spectral_index(
    image_id=scene_id,
    index_type="NDVI",
    nir_band="B8",
    red_band="B4",
)

print(f"Index formula applied: {ndvi_result['formula']}")
print(f"Output band: {ndvi_result['output_band']}")
```

---

## Step 3: Extracting Zonal Statistics

Next, calculate the mean vegetation vigor across a field polygon boundary using `ee_zonal_statistics`:

```python
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import ee_zonal_statistics

field_polygon = {
    "type": "Polygon",
    "coordinates": [[
        [-120.55, 36.50],
        [-120.45, 36.50],
        [-120.45, 36.58],
        [-120.55, 36.58],
        [-120.55, 36.50]
    ]]
}

stats = ee_zonal_statistics(
    image_id=scene_id,
    geometry_geojson=field_polygon,
    reducer="mean",
    scale_meters=20.0,
    bands=["B4", "B8"],
)

print("Field Mean Reflectance Values:")
for band, value in stats["statistics"].items():
    print(f"  {band}: {value}")
```

---

## Step 4: Generating a Visualization Thumbnail

Finally, request a 512x512 RGB preview thumbnail for visual verification:

```python
from plugins.geospatial_and_osint.earth_engine_imagery.main import ee_get_image_thumbnail_url

thumb = ee_get_image_thumbnail_url(
    image_id=scene_id,
    bands=["B4", "B3", "B2"],  # True color RGB
    min_val=0.0,
    max_val=3000.0,
    dimensions=512,
)

print(f"Preview URL: {thumb['thumbnail_url']}")
```

Congratulations! You have completed your first end-to-end satellite observation analysis pipeline with Brain Harness.
