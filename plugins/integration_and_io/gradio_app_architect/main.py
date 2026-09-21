"""Gradio App Architect Plugin — Production AI interface engineering and AST diagnostics.

Synthesized from Eva J Patel's literature:
'How to Use Gradio with Python: A Complete Beginner-to-Advanced Book' (freeCodeCamp, 2026).
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts and harness src directories are on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "gradio-app-architect" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gradio_app_engine import (  # noqa: E402
    AppScaffoldConfig,
    DiagnosticReport,
    GradioAppArchitectEngine,
)

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.gradio_app import (  # noqa: E402
    GRADIO_APP_ARCHITECT_SERVICE_KEY,
    AppScaffoldConfigData,
    AppScaffoldResultData,
    DiagnosticCheckData,
    DiagnosticReportData,
    GradioAppArchitectService,
)

logger = structlog.get_logger(__name__)


class GradioAppArchitectPlugin(HarnessPlugin, GradioAppArchitectService):
    """Plugin providing Gradio application AST diagnostics, scaffolding, and brief generation."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = GradioAppArchitectEngine()

    @property
    def name(self) -> str:
        return "plugin.gradio_app_architect"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Production AI interface engineering, AST diagnostic inspection, "
            "and scaffolding engine for Gradio (Eva J Patel 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GRADIO_APP_ARCHITECT_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container."""
        context.provide(GRADIO_APP_ARCHITECT_SERVICE_KEY, self)
        logger.info(
            "gradio_app_architect_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Cleanup upon unload."""
        logger.info("gradio_app_architect_plugin_unloaded")

    # --- GradioAppArchitectService Protocol Implementation ---

    def audit_code(self, source_code: str, file_path: str = "") -> DiagnosticReportData:
        """Run AST static analysis against the 5 production Gradio rubrics."""
        rep: DiagnosticReport = self._engine.audit_code(
            source_code, file_path=file_path or "<source>"
        )
        checks_data = [
            DiagnosticCheckData(
                rule_id=c.rule_id,
                name=c.name,
                passed=c.passed,
                message=c.message,
                severity=c.severity,
                line_number=c.line_number,
            )
            for c in rep.checks
        ]
        return DiagnosticReportData(
            target=rep.target,
            passed=rep.passed,
            checks=checks_data,
            metrics=rep.metrics,
        )

    def scaffold_app(self, config: AppScaffoldConfigData) -> AppScaffoldResultData:
        """Generate a decoupled production Gradio application."""
        cfg = AppScaffoldConfig(
            app_name=config.app_name,
            topology=config.topology,
            enable_queue=config.enable_queue,
            concurrency_limit=config.concurrency_limit,
            max_queue_size=config.max_queue_size,
            output_dir=config.output_dir,
        )
        res = self._engine.scaffold_app(cfg)
        return AppScaffoldResultData(
            files=dict(res.files),
            manifest=res.manifest,
        )

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and topology diagram."""
        return self._engine.generate_visual_brief(output_path=output_path)


# Rule 45: Export module-level singleton instance
plugin = GradioAppArchitectPlugin()
