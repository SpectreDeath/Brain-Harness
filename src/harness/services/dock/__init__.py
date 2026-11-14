"""Repository Dock Service: Manifest Inspection, Link Approval, Safety Gating, and Execution."""

from __future__ import annotations

from .manifest import build_generic_dock_manifest, load_dock_manifest
from .models import (
    DockApprovalDriftError,
    DockBoundaries,
    DockBoundaryViolationError,
    DockError,
    DockLinkRecord,
    DockManifest,
    DockManifestError,
    DockNotFoundError,
    DockPermissionError,
    DockPermissions,
    DockProcedure,
    DockProcedureCycleError,
    DockRunResult,
    DockStep,
    DockStepResult,
)
from .protocols import DOCK_SERVICE_KEY, DockService, logger  # noqa: F401
from .safety import (
    _CATASTROPHIC_PATTERNS,  # noqa: F401
    _CREDENTIAL_ACCESS_PATTERNS,  # noqa: F401
    check_command_safety,
)
from .service import DefaultDockService, resolve_dock_service

__all__ = [
    "DOCK_SERVICE_KEY",
    "DockApprovalDriftError",
    "DockBoundaries",
    "DockBoundaryViolationError",
    "DockError",
    "DockLinkRecord",
    "DockManifest",
    "DockManifestError",
    "DockNotFoundError",
    "DockPermissionError",
    "DockPermissions",
    "DockProcedure",
    "DockProcedureCycleError",
    "DockRunResult",
    "DockService",
    "DockStep",
    "DockStepResult",
    "DefaultDockService",
    "build_generic_dock_manifest",
    "check_command_safety",
    "load_dock_manifest",
    "resolve_dock_service",
]
