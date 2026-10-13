"""Service resolver for UncertaintyGuardService per AGENTS.md Rule 58."""

from __future__ import annotations

from pathlib import Path
import sys
import structlog

from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    UncertaintyGuardService,
)

from .adapter import UncertaintyEngineAdapter

logger = structlog.get_logger(__name__)

# Alias for backward compatibility
_EngineAdapter = UncertaintyEngineAdapter


def get_uncertainty_service(
    context: ServiceContext | None = None,
) -> UncertaintyGuardService:
    """Resolve UncertaintyGuardService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(UNCERTAINTY_GUARD_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.uncertainty_guard.main import (
            plugin as guard_plugin,
        )

        return guard_plugin
    except Exception as exc:
        logger.warning("uncertainty_guard_plugin_fallback_failed", error=str(exc))
        return UncertaintyEngineAdapter()


def resolve_uncertainty_service(
    context: ServiceContext | None = None,
) -> UncertaintyGuardService:
    """Single-seam resolver alias per Rule 58."""
    return get_uncertainty_service(context)
