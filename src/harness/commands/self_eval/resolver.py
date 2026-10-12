"""Service resolution helpers for self-eval commands."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

from harness.kernel.context import ServiceContext
from harness.services.self_evaluating_pipeline import (
    SELF_EVALUATING_PIPELINE_SERVICE_KEY,
    SelfEvaluatingPipelineService,
)

logger = structlog.get_logger(__name__)


def get_self_eval_service(
    context: ServiceContext | None = None,
) -> SelfEvaluatingPipelineService:
    """Resolve SelfEvaluatingPipelineService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(SELF_EVALUATING_PIPELINE_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.self_evaluating_pipeline.main import (
            plugin as eval_plugin,
        )

        return eval_plugin
    except Exception as exc:
        logger.warning(
            "self_evaluating_pipeline_plugin_fallback_failed", error=str(exc)
        )
        skill_scripts = (
            _ws_root / ".agents" / "skills" / "self-evaluating-ai-pipeline" / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))

        from harness.commands.self_eval.engine_adapter import (
            SelfEvaluatingPipelineEngineAdapter,
        )

        return SelfEvaluatingPipelineEngineAdapter()
