"""Single-seam IoC resolution functions for Data Management subsystem per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.services.data_management.protocols import (
    DATA_MANAGEMENT_SERVICE_KEY,
    DataManagementService,
)
from harness.services.data_management.service import BuiltinDataManagementService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

_DEFAULT_DATA_SERVICE = BuiltinDataManagementService()


def resolve_data_management_service(context: ServiceContext | None = None) -> DataManagementService:
    """Resolve the DataManagementService instance from context or fallback to default singleton."""
    if context is not None and context.has(DATA_MANAGEMENT_SERVICE_KEY):
        return context.require(DATA_MANAGEMENT_SERVICE_KEY)
    return _DEFAULT_DATA_SERVICE
