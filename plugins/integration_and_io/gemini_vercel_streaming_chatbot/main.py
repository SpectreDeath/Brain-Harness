"""Gemini & Vercel Streaming Chatbot Plugin — Plain-text chunk streaming architecture.

Synthesized from Johnson Samuel's literature:
'How to Build an AI Chatbot with Gemini and Vercel Serverless Functions 🚀' (freeCodeCamp, 2026).
Knowledge Item: ki_20260918_gemini_vercel_streaming.
"""

from __future__ import annotations

import sys
from pathlib import Path
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
    _REPO_ROOT / ".agents" / "skills" / "gemini-vercel-streaming-chatbot" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gemini_vercel_engine import (
    AuditReport,
    GeminiVercelStreamingEngine,
    ScaffoldConfig,
    StreamSimulationResult,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.gemini_vercel import (
    GEMINI_VERCEL_STREAMING_SERVICE_KEY,
    AuditCheckData,
    AuditReportData,
    GeminiVercelStreamingService,
    ScaffoldConfigData,
    ScaffoldResultData,
    StreamSimulationData,
)

logger = structlog.get_logger(__name__)


class GeminiVercelStreamingPlugin(HarnessPlugin, GeminiVercelStreamingService):
    """Plugin providing Gemini & Vercel streaming static analysis, scaffolding, and brief generation."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = GeminiVercelStreamingEngine()

    @property
    def name(self) -> str:
        return "plugin.gemini_vercel_streaming_chatbot"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Production AI chatbot engineering with Google Gemini & Vercel Serverless "
            "plain-text chunk streaming (Johnson Samuel 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GEMINI_VERCEL_STREAMING_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container."""
        context.provide(GEMINI_VERCEL_STREAMING_SERVICE_KEY, self)
        logger.info(
            "gemini_vercel_streaming_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Cleanup upon unload."""
        logger.info("gemini_vercel_streaming_plugin_unloaded")

    # --- GeminiVercelStreamingService Protocol Implementation ---

    def audit_code(self, source_code: str, file_path: str = "") -> AuditReportData:
        """Run static analysis against the 5 production streaming rubrics."""
        rep: AuditReport = self._engine.audit_code(
            source_code, file_path=file_path or "<source>"
        )
        checks_data = [
            AuditCheckData(
                rule_id=c.rule_id,
                name=c.name,
                passed=c.passed,
                message=c.message,
                severity=c.severity,
                line_number=c.line_number,
            )
            for c in rep.checks
        ]
        return AuditReportData(
            target=rep.target,
            passed=rep.passed,
            checks=checks_data,
            metrics=rep.metrics,
        )

    def scaffold_app(self, config: ScaffoldConfigData) -> ScaffoldResultData:
        """Generate a production 3-tier Gemini & Vercel streaming application."""
        cfg = ScaffoldConfig(
            app_name=config.app_name,
            framework=config.framework,
            language=config.language,
            model=config.model,
            max_text_length=config.max_text_length,
            max_array_length=config.max_array_length,
            allowed_origin=config.allowed_origin,
            output_dir=config.output_dir,
        )
        res = self._engine.scaffold_app(cfg)
        return ScaffoldResultData(
            files=dict(res.files),
            manifest=res.manifest,
        )

    def simulate_stream(self, prompt: str, chunks_count: int = 5) -> StreamSimulationData:
        """Simulate unbuffered plain-text chunk streaming."""
        sim_res: StreamSimulationResult = self._engine.simulate_stream(
            prompt=prompt, chunks_count=chunks_count
        )
        return StreamSimulationData(
            prompt=sim_res.prompt,
            chunks=list(sim_res.chunks),
            reconstructed_text=sim_res.reconstructed_text,
            total_chunks=sim_res.total_chunks,
            duration_ms=sim_res.duration_ms,
        )

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and topology diagram."""
        return self._engine.generate_visual_brief(output_path=output_path)


# Rule 45: Export module-level singleton instance
plugin = GeminiVercelStreamingPlugin()
