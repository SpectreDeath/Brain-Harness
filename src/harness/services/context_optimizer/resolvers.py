"""Single-seam IoC resolution factory for ContextOptimizerService (Rule 58)."""

from __future__ import annotations

import sys
import structlog

from harness.kernel.context import ServiceContext
from harness.services.context_optimizer.models import ContextOptimizationConfig
from harness.services.context_optimizer.protocols import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    ContextOptimizerService,
)
from harness.services.context_optimizer.service import DefaultContextOptimizerService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.services.context_optimizer.resolvers")


def resolve_context_optimizer(
    ctx: ServiceContext | None = None,
    config: ContextOptimizationConfig | None = None,
) -> ContextOptimizerService:
    """Resolve ContextOptimizerService from IoC container with fallback to DefaultContextOptimizerService."""
    if ctx is not None:
        try:
            svc = ctx.optional(CONTEXT_OPTIMIZER_SERVICE_KEY)
            if svc is not None:
                return svc
            legacy_svc = ctx.optional(AGENT_CONTEXT_OPTIMIZER_KEY)
            if legacy_svc is not None:
                return legacy_svc
        except Exception as err:
            logger.debug("Failed resolving context optimizer from context: %s", err)

    return DefaultContextOptimizerService(config=config, context=ctx)


__all__ = [
    "resolve_context_optimizer",
]
