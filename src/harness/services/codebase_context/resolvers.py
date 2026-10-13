"""Single-seam resolver for Codebase Context Service per Rule 58."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from harness.kernel.context import ServiceContext
from .protocol import CODEBASE_CONTEXT_SERVICE_KEY, CodebaseContextService
from .service import DefaultCodebaseContextService

logger = logging.getLogger("harness.services.codebase_context.resolvers")


def resolve_codebase_context(
    ctx: Optional[ServiceContext] = None,
    root: str | Path = ".",
) -> CodebaseContextService:
    """Resolve CodebaseContextService from IoC container with fallback to DefaultCodebaseContextService."""
    if ctx is not None:
        try:
            svc = ctx.optional(CODEBASE_CONTEXT_SERVICE_KEY)
            if svc is not None:
                return svc
        except Exception as err:
            logger.debug("Failed resolving CODEBASE_CONTEXT_SERVICE_KEY from context: %s", err)

    return DefaultCodebaseContextService(root=root)
