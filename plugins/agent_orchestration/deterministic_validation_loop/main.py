"""Deterministic Validation Loop Plugin — Spec-First Validation Hierarchy.

Implements the spec-first deterministic validation loop methodology
derived from Manish Ramavat (freeCodeCamp, 2026).
"""

from __future__ import annotations

import json
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

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "deterministic-validation-loop" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from validation_loop_engine import (  # type: ignore
    DeterministicValidationEngine,
    LoopExecutionResult,
    ValidationReport,
    ValidationSpec,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.deterministic_validation import (
    DETERMINISTIC_VALIDATION_SERVICE_KEY,
    DeterministicValidationService,
    LoopExecutionResultData,
    TriageRecordData,
    ValidationResultData,
)

logger = structlog.get_logger(__name__)


class DeterministicValidationPlugin(HarnessPlugin, DeterministicValidationService):
    """Plugin providing in-memory 3-tier deterministic validation, loop execution, and visual briefs."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = DeterministicValidationEngine()

    @property
    def name(self) -> str:
        return "plugin.deterministic_validation_loop"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Spec-first 3-tier deterministic validation loops with delta feedback "
            "injection and bounded retries"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DETERMINISTIC_VALIDATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the DeterministicValidationService into the IoC container."""
        context.provide(DETERMINISTIC_VALIDATION_SERVICE_KEY, self)
        logger.info(
            "deterministic_validation_service_provided",
            service=str(DETERMINISTIC_VALIDATION_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    # --- Service Protocol Implementation ---

    def _resolve_spec(self, spec: str | dict[str, Any]) -> ValidationSpec:
        """Resolve a specification name or raw schema dictionary into a ValidationSpec."""
        if isinstance(spec, str):
            preset = self._engine.get_preset(spec)
            if preset is not None:
                return preset
            # Try parsing string as JSON schema
            try:
                schema_dict = json.loads(spec)
                return ValidationSpec(name="dynamic_schema", schema=schema_dict)
            except Exception:
                raise ValueError(
                    f"Unknown preset '{spec}' and input is not valid JSON schema string."
                )
        elif isinstance(spec, dict):
            return ValidationSpec(
                name=spec.get("name", "custom_schema"),
                schema=spec.get("schema", spec),
            )
        raise TypeError(f"Expected str or dict for spec, got {type(spec)}")

    def validate(
        self,
        payload: dict[str, Any],
        spec: str | dict[str, Any] = "deployment_config",
    ) -> ValidationResultData:
        """Validate payload against a preset or schema."""
        resolved_spec = self._resolve_spec(spec)
        report: ValidationReport = self._engine.validate(resolved_spec, payload)
        return ValidationResultData(
            is_valid=report.is_valid,
            errors=list(report.errors),
            tier_failures=[t.value for t in report.tier_failures],
            duration_ms=report.duration_ms,
        )

    def execute_loop(
        self,
        request: str,
        generator: Any,
        spec: str | dict[str, Any] = "deployment_config",
        max_attempts: int = 3,
    ) -> LoopExecutionResultData:
        """Execute state machine loop with delta error injection and bounded budget."""
        resolved_spec = self._resolve_spec(spec)
        result: LoopExecutionResult = self._engine.run_loop(
            request=request,
            generator_func=generator,
            spec=resolved_spec,
            max_attempts=max_attempts,
        )

        triage_data = None
        if result.triage_record:
            triage_data = TriageRecordData(
                request=result.triage_record.request,
                final_errors=list(result.triage_record.final_errors),
                attempts=result.triage_record.attempts,
                error_code=result.triage_record.error_code,
                timestamp=result.triage_record.timestamp,
            )

        return LoopExecutionResultData(
            status=result.status,
            payload=result.payload,
            attempts=result.attempts,
            errors=list(result.errors),
            triage_record=triage_data,
            trace=list(result.trace),
        )

    def format_feedback(self, request: str, errors: list[str]) -> str:
        """Format unambiguous error strings for LLM delta injection."""
        return self._engine.format_error_feedback(request, errors)

    def get_preset_spec(self, name: str) -> dict[str, Any] | None:
        """Retrieve schema dictionary for a built-in preset."""
        preset = self._engine.get_preset(name)
        if preset:
            return {"name": preset.name, "schema": preset.schema}
        return None

    def list_presets(self) -> list[str]:
        """List registered preset specification names."""
        return self._engine.list_presets()

    def visual_brief(
        self,
        result: Any,
        title: str = "Deterministic Validation Brief",
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief with execution trace."""
        return self._engine.generate_visual_brief(
            result, title=title, output_path=output_path
        )

    # --- Tool Invocation Handlers ---

    async def validate_payload(self, **kwargs: Any) -> dict[str, Any]:
        """Tool handler for validating a payload."""
        payload = kwargs.get("payload")
        spec = kwargs.get("spec", "deployment_config")
        if not isinstance(payload, dict):
            return {
                "is_valid": False,
                "errors": ["payload parameter must be a JSON object dictionary"],
            }
        res = self.validate(payload, spec)
        return res.model_dump()

    async def run_validation_loop(self, **kwargs: Any) -> dict[str, Any]:
        """Tool handler for running validation loop with static or simulated output."""
        request = kwargs.get("request", "")
        spec = kwargs.get("spec", "deployment_config")
        max_attempts = int(kwargs.get("max_attempts", 3))

        # Generator stub returning valid payload for preset if available
        def mock_generator(req: str, errors: list[str], attempt: int) -> dict[str, Any]:
            if spec == "deployment_config":
                return {
                    "service_name": "app-service",
                    "replicas": 3,
                    "resources": {"cpu_limit": 1.0, "memory_limit_mb": 512},
                    "health_check": {
                        "path": "/healthz",
                        "timeout_seconds": 2,
                        "interval_seconds": 10,
                    },
                }
            return {}

        res = self.execute_loop(
            request, mock_generator, spec=spec, max_attempts=max_attempts
        )
        return res.model_dump()

    async def get_preset_spec_tool(self, **kwargs: Any) -> dict[str, Any]:
        """Tool handler for retrieving preset schema."""
        name = kwargs.get("name", "")
        res = self.get_preset_spec(name)
        if res is None:
            return {"error": f"Preset '{name}' not found"}
        return res

    async def validation_visual_brief(self, **kwargs: Any) -> str:
        """Tool handler for generating visual brief."""
        output_path = kwargs.get("output_path")
        report = self.validate(
            {
                "service_name": "sample-service",
                "replicas": 2,
                "resources": {"cpu_limit": 0.5, "memory_limit_mb": 256},
                "health_check": {
                    "path": "/health",
                    "timeout_seconds": 2,
                    "interval_seconds": 10,
                },
            }
        )
        path = self.visual_brief(report, output_path=output_path)
        return str(path)


# Module-level singleton required by Rule 45
plugin = DeterministicValidationPlugin()
