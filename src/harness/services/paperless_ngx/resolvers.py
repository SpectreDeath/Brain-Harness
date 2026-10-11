"""Single-seam IoC resolution functions for Paperless-NGX subsystem per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.services.paperless_ngx.models import PaperlessConfig
from harness.services.paperless_ngx.protocols import (
    PAPERLESS_NGX_SERVICE_KEY,
    PaperlessNgxService,
)
from harness.services.paperless_ngx.service import DefaultPaperlessNgxService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

_DEFAULT_PAPERLESS_SERVICE = DefaultPaperlessNgxService(PaperlessConfig())


def resolve_paperless_ngx_service(
    context: ServiceContext | None = None,
) -> PaperlessNgxService:
    """Resolve the PaperlessNgxService instance from context or fallback to default singleton."""
    if context is not None and context.has(PAPERLESS_NGX_SERVICE_KEY):
        return context.require(PAPERLESS_NGX_SERVICE_KEY)
    return _DEFAULT_PAPERLESS_SERVICE
