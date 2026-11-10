"""Typed service keys for recursive harnessing (Rule 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.services.recursive_harnessing.protocols import (
        EvidenceIsolationService,
        RecursiveRefinerService,
    )

EVIDENCE_ISOLATION_SERVICE_KEY = ServiceKey["EvidenceIsolationService"]("service.evidence_isolation")
RECURSIVE_REFINER_SERVICE_KEY = ServiceKey["RecursiveRefinerService"]("service.recursive_refiner")
