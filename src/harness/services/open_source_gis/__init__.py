"""Open-Source GIS Architect Service, domain models, and deterministic routing engine.

Provides analytical fitness matching across 14 open-source GIS engines,
CRS planar projection safety verification, geometric topology auditing,
automated HTML visual brief generation, and single-seam resolver factory.

Enforces:
- Rule 1: Everything is a plugin (registered via IoC container)
- Rule 2: Service keys are typed (OPEN_SOURCE_GIS_SERVICE_KEY)
- Rule 12: Slotted & frozen dataclasses
- Rule 43: Direct attribute mutation assertion invariants
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 51: Multi-brace escaping in HTML/CSS templates
- Rule 58: Single-seam resolver factory (resolve_open_source_gis)
"""

from __future__ import annotations

from harness.services.open_source_gis.catalog import GISEngineCatalog
from harness.services.open_source_gis.models import (
    CRSProjectionError,
    EngineSelectionResult,
    FalconViewRestrictedDomainError,
    GISEngineRecord,
    GISEngineScore,
    GisVisualBriefResult,
    SpatialArchitectureReceipt,
    SpatialPipelineDAG,
    SpatialPipelineStep,
    SpatialWorkloadProfile,
    TopologyAuditReport,
    TopologyValidationError,
)
from harness.services.open_source_gis.service import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    DefaultOpenSourceGisService,
    OpenSourceGisService,
    resolve_open_source_gis,
)
from harness.services.open_source_gis.validator import (
    audit_topology,
    validate_pipeline_dag,
)
from harness.services.open_source_gis.visualizer import generate_visual_brief

__all__ = [
    "CRSProjectionError",
    "DefaultOpenSourceGisService",
    "EngineSelectionResult",
    "FalconViewRestrictedDomainError",
    "GISEngineCatalog",
    "GISEngineRecord",
    "GISEngineScore",
    "GisVisualBriefResult",
    "OPEN_SOURCE_GIS_SERVICE_KEY",
    "OpenSourceGisService",
    "SpatialArchitectureReceipt",
    "SpatialPipelineDAG",
    "SpatialPipelineStep",
    "SpatialWorkloadProfile",
    "TopologyAuditReport",
    "TopologyValidationError",
    "audit_topology",
    "generate_visual_brief",
    "resolve_open_source_gis",
    "validate_pipeline_dag",
]
