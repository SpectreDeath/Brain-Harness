"""Typed service keys for PyRIT Red-Teaming Scanner (Rule 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.services.pyrit_scanner.protocols import PyritScannerService

PYRIT_SCANNER_SERVICE_KEY = ServiceKey["PyritScannerService"]("service.pyrit_scanner")
