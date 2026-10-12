"""Service resolution helpers for coding harness calibrator commands."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

from harness.kernel.context import ServiceContext
from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    CodingHarnessCalibratorService,
)

logger = structlog.get_logger(__name__)


def get_calibrator_service(
    context: ServiceContext | None = None,
) -> CodingHarnessCalibratorService:
    """Resolve CodingHarnessCalibratorService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(CODING_HARNESS_CALIBRATOR_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.coding_harness_calibrator.main import (
            plugin as calibrator_plugin,
        )

        return calibrator_plugin
    except Exception as exc:
        logger.warning(
            "coding_harness_calibrator_plugin_fallback_failed", error=str(exc)
        )
        from harness.commands.calibrator.engine_adapter import (
            CodingHarnessCalibratorEngineAdapter,
        )

        return CodingHarnessCalibratorEngineAdapter()
