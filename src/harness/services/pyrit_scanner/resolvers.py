"""Single-seam resolver for PyritScannerService."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from harness.services.pyrit_scanner.keys import PYRIT_SCANNER_SERVICE_KEY
from harness.services.pyrit_scanner.protocols import PyritScannerService
from harness.services.pyrit_scanner.service import DefaultPyritScannerService


def resolve_pyrit_scanner(context: ServiceContext | None = None) -> PyritScannerService:
    """Resolve PyritScannerService from context or return DefaultPyritScannerService."""
    if context is not None and hasattr(context, "has") and context.has(PYRIT_SCANNER_SERVICE_KEY):
        return context.require(PYRIT_SCANNER_SERVICE_KEY)
    return DefaultPyritScannerService()
