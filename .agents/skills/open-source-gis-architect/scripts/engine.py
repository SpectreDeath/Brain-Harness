"""Slotted and frozen domain models and deterministic routing engine for open-source GIS software.

Elevated to harness.services.open_source_gis under Rule 49; this module provides
a thin, 100% backward-compatible facade for existing standalone skill scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace src is accessible if imported in standalone context
_src_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "src"
if _src_path.exists() and str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from harness.services.open_source_gis import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    CRSProjectionError,
    DefaultOpenSourceGisService,
    EngineSelectionResult,
    FalconViewRestrictedDomainError,
    GISEngineCatalog,
    GISEngineRecord,
    GISEngineScore,
    GisVisualBriefResult,
    OpenSourceGisService,
    SpatialArchitectureReceipt,
    SpatialPipelineDAG,
    SpatialPipelineStep,
    SpatialWorkloadProfile,
    TopologyAuditReport,
    TopologyValidationError,
)

__all__ = [
    "OPEN_SOURCE_GIS_SERVICE_KEY",
    "CRSProjectionError",
    "DefaultOpenSourceGisService",
    "EngineSelectionResult",
    "FalconViewRestrictedDomainError",
    "GISEngineCatalog",
    "GISEngineRecord",
    "GISEngineScore",
    "GisVisualBriefResult",
    "OpenSourceGisService",
    "SpatialArchitectureReceipt",
    "SpatialPipelineDAG",
    "SpatialPipelineStep",
    "SpatialWorkloadProfile",
    "TopologyAuditReport",
    "TopologyValidationError",
]
