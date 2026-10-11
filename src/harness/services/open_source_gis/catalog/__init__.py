"""Decomposed open-source GIS engine catalog and deterministic router facade."""

from __future__ import annotations

from harness.services.open_source_gis.catalog.core import GISEngineCatalog
from harness.services.open_source_gis.catalog.environmental_paths import try_environmental_routes
from harness.services.open_source_gis.catalog.fallback import get_fallback_engine_catalog
from harness.services.open_source_gis.catalog.loader import (
    find_resource_file,
    load_default_catalog,
    load_default_weights,
)
from harness.services.open_source_gis.catalog.router import route_workload
from harness.services.open_source_gis.catalog.statistical_paths import try_statistical_routes
from harness.services.open_source_gis.catalog.vector_web_paths import try_vector_web_routes

__all__ = [
    "GISEngineCatalog",
    "find_resource_file",
    "get_fallback_engine_catalog",
    "load_default_catalog",
    "load_default_weights",
    "route_workload",
    "try_environmental_routes",
    "try_statistical_routes",
    "try_vector_web_routes",
]
