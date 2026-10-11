"""Curated Earth Engine Data Catalog Index and discovery query operations."""

from __future__ import annotations

from typing import Any

CATALOG_DATASETS: list[dict[str, Any]] = [
    {
        "id": "COPERNICUS/S2_SR_HARMONIZED",
        "title": "Sentinel-2 MSI: MultiSpectral Instrument, Level-2A",
        "category": "imagery",
        "tags": ["sentinel", "copernicus", "msi", "multispectral", "surface_reflectance"],
        "spatial_resolution_meters": 10.0,
        "time_start": "2017-03-28",
        "description": "High-resolution wide-swath multispectral imagery with 13 spectral bands in the VNIR and SWIR.",
    },
    {
        "id": "LANDSAT/LC08/C02/T1_L2",
        "title": "USGS Landsat 8 Level 2, Collection 2, Tier 1",
        "category": "imagery",
        "tags": ["landsat", "usgs", "nasa", "thermal", "surface_reflectance"],
        "spatial_resolution_meters": 30.0,
        "time_start": "2013-03-18",
        "description": "Atmospherically corrected surface reflectance and surface temperature from the Landsat 8 OLI/TIRS sensor.",
    },
    {
        "id": "USGS/3DEP/10m",
        "title": "USGS 3D Elevation Program (3DEP) 10m Bare Earth DEM",
        "category": "elevation",
        "tags": ["dem", "elevation", "usgs", "topography", "3dep"],
        "spatial_resolution_meters": 10.0,
        "time_start": "2019-01-01",
        "description": "High-accuracy digital elevation models for the contiguous United States, Hawaii, and territories.",
    },
    {
        "id": "NASA/NASADEM_HGT/001",
        "title": "NASADEM: Global Elevation Model 30m",
        "category": "elevation",
        "tags": ["dem", "elevation", "nasa", "global", "srtm"],
        "spatial_resolution_meters": 30.0,
        "time_start": "2000-02-11",
        "description": "Reprocessed SRTM data combined with ASTER GDEM, ICESat, and PRISM global topographic data.",
    },
    {
        "id": "ECMWF/ERA5_LAND/HOURLY",
        "title": "ERA5-Land Hourly - ECMWF Climate Reanalysis",
        "category": "climate",
        "tags": ["weather", "climate", "ecmwf", "temperature", "precipitation", "wind"],
        "spatial_resolution_meters": 9000.0,
        "time_start": "1950-01-01",
        "description": "Enhanced global atmospheric and surface climate reanalysis dataset with hourly frequency.",
    },
    {
        "id": "MODIS/061/MOD13Q1",
        "title": "MODIS/Terra Vegetation Indices 16-Day L3 Global 250m",
        "category": "landcover",
        "tags": ["modis", "ndvi", "evi", "vegetation", "global"],
        "spatial_resolution_meters": 250.0,
        "time_start": "2000-02-18",
        "description": "Global Normalized Difference Vegetation Index (NDVI) and Enhanced Vegetation Index (EVI) composites.",
    },
    {
        "id": "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
        "title": "VIIRS Nighttime Day/Night Band Monthly Cloud-Free Composites",
        "category": "imagery",
        "tags": ["nighttime_lights", "viirs", "noaa", "radiance", "urban"],
        "spatial_resolution_meters": 463.0,
        "time_start": "2014-01-01",
        "description": "Monthly nighttime radiance composites filter out stray light and cloud cover for electrification and economic modeling.",
    },
    {
        "id": "JRC/GSW1_4/GlobalSurfaceWater",
        "title": "JRC Global Surface Water Mapping (1984-2021)",
        "category": "oceans",
        "tags": ["water", "hydrology", "jrc", "lakes", "rivers", "flooding"],
        "spatial_resolution_meters": 30.0,
        "time_start": "1984-03-16",
        "description": "Maps the location and temporal distribution of surface water globally over 38 years.",
    },
]


def query_data_catalog(
    query: str = "",
    category: str = "",
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search and discover datasets in the public Earth Engine Data Catalog."""
    q = (query or "").lower().strip()
    cat = (category or "").lower().strip()
    tag_list = [t.lower().strip() for t in (tags or [])]

    results = []
    for ds in CATALOG_DATASETS:
        if cat and ds["category"] != cat:
            continue
        if tag_list and not any(t in ds["tags"] for t in tag_list):
            continue
        if q:
            searchable = f"{ds['id']} {ds['title']} {ds['description']} {' '.join(ds['tags'])}".lower()
            if q not in searchable:
                continue

        results.append(ds)
        if len(results) >= limit:
            break

    return {
        "status": "ok",
        "query": query,
        "category": category,
        "tags": tags or [],
        "total_found": len(results),
        "datasets": results,
    }
