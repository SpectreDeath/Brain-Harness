"""Deterministic routing coordinator across specialized open-source GIS engine paths."""

from __future__ import annotations

from harness.services.open_source_gis.catalog.environmental_paths import try_environmental_routes
from harness.services.open_source_gis.catalog.statistical_paths import try_statistical_routes
from harness.services.open_source_gis.catalog.vector_web_paths import try_vector_web_routes
from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    SpatialWorkloadProfile,
)


def route_workload(
    engines_by_name: dict[str, GISEngineRecord],
    profile: SpatialWorkloadProfile,
    weights: dict[str, float] | None = None,
) -> EngineSelectionResult:
    """Route workload to optimal primary and secondary GIS engines using deterministic paths."""
    env_result = try_environmental_routes(engines_by_name, profile)
    if env_result is not None:
        return env_result

    stat_result = try_statistical_routes(engines_by_name, profile)
    if stat_result is not None:
        return stat_result

    vec_result = try_vector_web_routes(engines_by_name, profile)
    if vec_result is not None:
        return vec_result

    fallback_profile = SpatialWorkloadProfile(domain="cartography", analysis="mapping")
    fallback_res = try_vector_web_routes(engines_by_name, fallback_profile)
    assert fallback_res is not None
    return fallback_res
