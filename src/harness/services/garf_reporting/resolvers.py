"""Single-seam resolver for Garf Reporting Service per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import GARF_REPORTING_SERVICE_KEY, GarfReportingService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext


def resolve_garf_reporting(
    target: Any = None,
    **kwargs: Any,
) -> GarfReportingService:
    """Resolve or instantiate authoritative GarfReportingService instance (Rule 58).

    Args:
        target: Optional ServiceContext, existing service instance, or None.
        **kwargs: Optional constructor arguments passed if instantiated.

    Returns:
        Authoritative GarfReportingService instance.
    """
    from .core import DefaultGarfReportingService

    if target is None:
        return DefaultGarfReportingService(**kwargs)

    if isinstance(target, GarfReportingService):
        return target

    if hasattr(target, "optional") and hasattr(target, "provide"):
        existing = target.optional(GARF_REPORTING_SERVICE_KEY)
        if existing is not None and isinstance(existing, GarfReportingService):
            return existing
        service = DefaultGarfReportingService(**kwargs)
        target.provide(GARF_REPORTING_SERVICE_KEY, service)
        return service

    return DefaultGarfReportingService(**kwargs)
