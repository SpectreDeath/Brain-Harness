"""Single-seam resolvers for recursive-harnessing services (Rules 49, 58).

A registered service is returned as-is: callers get partial or mock implementations through the
same seam, so no `isinstance`/protocol gate may reject them (Rule 58).
"""

from __future__ import annotations

from typing import Any

from harness.services.recursive_harnessing.keys import (
    EVIDENCE_ISOLATION_SERVICE_KEY,
    RECURSIVE_REFINER_SERVICE_KEY,
)
from harness.services.recursive_harnessing.protocols import EvidenceIsolationService, RecursiveRefinerService
from harness.services.recursive_harnessing.service import (
    DefaultEvidenceIsolationService,
    DefaultRecursiveRefinerService,
)


def _registered(context: Any, key: Any) -> Any | None:
    if context is not None and hasattr(context, "has") and context.has(key):
        return context.require(key)
    return None


def resolve_evidence_isolation(context: Any | None = None) -> EvidenceIsolationService:
    """The registered evidence-isolation service, else the default implementation."""
    return _registered(context, EVIDENCE_ISOLATION_SERVICE_KEY) or DefaultEvidenceIsolationService()


def resolve_recursive_refiner(context: Any | None = None) -> RecursiveRefinerService:
    """The registered recursive-refiner service, else the default implementation."""
    return _registered(context, RECURSIVE_REFINER_SERVICE_KEY) or DefaultRecursiveRefinerService()
