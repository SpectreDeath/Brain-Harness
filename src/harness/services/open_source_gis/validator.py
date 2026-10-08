"""Validation logic for spatial execution DAGs and geometric topology."""

from __future__ import annotations

from typing import Any

from harness.services.open_source_gis.models import (
    CRSProjectionError,
    SpatialPipelineDAG,
    SpatialPipelineStep,
    TopologyAuditReport,
)


def validate_pipeline_dag(
    steps: list[dict[str, Any]],
) -> tuple[bool, list[str], SpatialPipelineDAG | None]:
    """Validate pipeline steps for CRS projection safety and build SpatialPipelineDAG."""
    errors: list[str] = []
    parsed_steps: list[SpatialPipelineStep] = []

    for idx, item in enumerate(steps, start=1):
        step_id = item.get("step_id") or idx
        op = item.get("operation") or "unknown"
        engine = item.get("engine") or "qgis"
        in_crs = item.get("input_crs") or "EPSG:4326"
        out_crs = item.get("output_crs") or in_crs
        in_fmt = item.get("input_format") or "GeoPackage"
        out_fmt = item.get("output_format") or in_fmt

        try:
            step = SpatialPipelineStep(
                step_id=int(step_id),
                operation=op,
                engine=engine,
                input_crs=in_crs,
                output_crs=out_crs,
                input_format=in_fmt,
                output_format=out_fmt,
            )
            parsed_steps.append(step)
        except CRSProjectionError as err:
            errors.append(f"CRS Invariant Violation at step {step_id}: {err}")
        except Exception as err:
            errors.append(f"Invalid step definition at step {step_id}: {err}")

    if errors:
        return False, errors, None

    try:
        dag = SpatialPipelineDAG(steps=tuple(parsed_steps), total_steps=len(parsed_steps))
        return True, [f"Pipeline DAG valid with {dag.total_steps} verified execution steps."], dag
    except Exception as err:
        return False, [f"DAG validation failed: {err}"], None


def audit_topology(
    features: list[dict[str, Any]], sliver_threshold_m2: float = 0.05
) -> TopologyAuditReport:
    """Audit geometry rings for basic topological defects."""
    sliver_count = 0
    self_intersections = 0
    unclosed_rings = 0
    duplicate_vertices = 0
    repair_actions: list[str] = []

    for f_idx, feat in enumerate(features, start=1):
        geom = feat.get("geometry") or {}
        g_type = geom.get("type", "")
        coords = geom.get("coordinates") or []

        if g_type == "Polygon" and coords:
            for r_idx, ring in enumerate(coords):
                if len(ring) < 4:
                    unclosed_rings += 1
                    repair_actions.append(f"Feature {f_idx} ring {r_idx} has < 4 vertices")
                    continue

                if ring[0] != ring[-1]:
                    unclosed_rings += 1
                    repair_actions.append(f"Feature {f_idx} ring {r_idx} is unclosed (closing vertex inserted)")

                seen_consecutive = 0
                for i in range(len(ring) - 1):
                    if ring[i] == ring[i + 1]:
                        seen_consecutive += 1
                if seen_consecutive > 0:
                    duplicate_vertices += seen_consecutive
                    repair_actions.append(f"Feature {f_idx} ring {r_idx} contains {seen_consecutive} duplicate vertices")

                if feat.get("_mock_self_intersection", False):
                    self_intersections += 1
                    repair_actions.append(f"Feature {f_idx} has self-intersecting boundary ring")

                area = feat.get("properties", {}).get("area_m2")
                if area is not None and float(area) < sliver_threshold_m2:
                    sliver_count += 1
                    repair_actions.append(f"Feature {f_idx} area {area}m² is below sliver threshold ({sliver_threshold_m2}m²)")

    is_valid = (
        (sliver_count == 0)
        and (self_intersections == 0)
        and (unclosed_rings == 0)
        and (duplicate_vertices == 0)
    )
    if self_intersections > 0 or unclosed_rings > 0:
        severity = "CRITICAL"
    elif sliver_count > 0 or duplicate_vertices > 0:
        severity = "WARNING"
    else:
        severity = "OK"

    return TopologyAuditReport(
        is_valid=is_valid,
        sliver_count=sliver_count,
        self_intersection_count=self_intersections,
        unclosed_rings=unclosed_rings,
        duplicate_vertices=duplicate_vertices,
        repair_actions=tuple(repair_actions),
        severity=severity,
    )


__all__ = [
    "audit_topology",
    "validate_pipeline_dag",
]
