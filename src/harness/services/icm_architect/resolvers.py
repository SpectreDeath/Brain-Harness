"""Single-seam resolver for IcmArchitectService adhering to Rule 58."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from .protocol import ICM_ARCHITECT_SERVICE_KEY, IcmArchitectService
from .service import DefaultIcmArchitectService

logger = structlog.get_logger(__name__)

_DEFAULT_INSTANCE = DefaultIcmArchitectService()


def resolve_icm_architect_service(context: ServiceContext | None = None) -> IcmArchitectService:
    """Resolve IcmArchitectService from IoC container with singleton fallback."""
    if context is not None:
        try:
            svc = context.optional(ICM_ARCHITECT_SERVICE_KEY)
            if svc is not None:
                return svc
        except Exception as err:
            logger.debug("Failed resolving ICM_ARCHITECT_SERVICE_KEY from context: %s", err)
    return _DEFAULT_INSTANCE
