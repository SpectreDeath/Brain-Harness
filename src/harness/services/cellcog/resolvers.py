"""Single-seam IoC resolution functions for the CellCog service subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.services.cellcog.protocols import CELLCOG_SERVICE_KEY, CellCogServiceProtocol
from harness.services.cellcog.service import CellCogService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

_DEFAULT_CELLCOG_SERVICE = CellCogService()


def resolve_cellcog_service(context: ServiceContext | None = None) -> CellCogServiceProtocol:
    """Resolve the CellCog service instance from context or fallback to default singleton."""
    if context is not None and context.has(CELLCOG_SERVICE_KEY):
        return context.require(CELLCOG_SERVICE_KEY)
    return _DEFAULT_CELLCOG_SERVICE
