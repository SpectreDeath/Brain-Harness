"""Deterministic Validation Loop CLI commands.

Provides headless Click CLI introspection for 3-tier validation,
spec inspections, loop simulation, and visual HTML briefs.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.deterministic_validation import (
    DETERMINISTIC_VALIDATION_SERVICE_KEY,
    DeterministicValidationService,
    LoopExecutionResultData,
    ValidationResultData,
)

logger = structlog.get_logger(__name__)


def get_validation_service(
    context: ServiceContext | None = None,
) -> DeterministicValidationService:
    """Resolve DeterministicValidationService from context or fall back to plugin singleton / engine."""
    if context is not None:
        svc = context.optional(DETERMINISTIC_VALIDATION_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.deterministic_validation_loop.main import (
            plugin as val_plugin,
        )

        return val_plugin
    except Exception as exc:
        logger.warning(
            "deterministic_validation_plugin_fallback_failed", error=str(exc)
        )
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "deterministic-validation-loop"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from validation_loop_engine import (  # type: ignore
            DeterministicValidationEngine,
            ValidationSpec,
        )

        class _EngineAdapter(DeterministicValidationService):
            def __init__(self) -> None:
                self._eng = DeterministicValidationEngine()

            def _get_spec(self, spec: str | dict[str, Any]) -> ValidationSpec:
                if isinstance(spec, str):
                    s = self._eng.get_preset(spec)
                    if s:
                        return s
                    return ValidationSpec(name="dynamic", schema=_json.loads(spec))
                return ValidationSpec(
                    name=spec.get("name", "custom"),
                    schema=spec.get("schema", spec),
                )

            def validate(
                self, payload: dict[str, Any], spec: str | dict[str, Any]
            ) -> ValidationResultData:
                s = self._get_spec(spec)
                rep = self._eng.validate(s, payload)
                return ValidationResultData(
                    is_valid=rep.is_valid,
                    errors=list(rep.errors),
                    tier_failures=[t.value for t in rep.tier_failures],
                    duration_ms=rep.duration_ms,
                )

            def execute_loop(
                self,
                request: str,
                generator: Any,
                spec: str | dict[str, Any],
                max_attempts: int = 3,
            ) -> LoopExecutionResultData:
                s = self._get_spec(spec)
                res = self._eng.run_loop(request, generator, s, max_attempts)
                from harness.services.deterministic_validation import (
                    TriageRecordData,
                )

                t_data = None
                if res.triage_record:
                    t_data = TriageRecordData(
                        request=res.triage_record.request,
                        final_errors=list(res.triage_record.final_errors),
                        attempts=res.triage_record.attempts,
                        error_code=res.triage_record.error_code,
                        timestamp=res.triage_record.timestamp,
                    )
                return LoopExecutionResultData(
                    status=res.status,
                    payload=res.payload,
                    attempts=res.attempts,
                    errors=list(res.errors),
                    triage_record=t_data,
                    trace=list(res.trace),
                )

            def format_feedback(self, request: str, errors: list[str]) -> str:
                return self._eng.format_error_feedback(request, errors)

            def get_preset_spec(self, name: str) -> dict[str, Any] | None:
                p = self._eng.get_preset(name)
                return {"name": p.name, "schema": p.schema} if p else None

            def list_presets(self) -> list[str]:
                return self._eng.list_presets()

            def visual_brief(
                self,
                result: Any,
                title: str = "Deterministic Validation Brief",
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.generate_visual_brief(
                    result, title=title, output_path=output_path
                )

        return _EngineAdapter()


@click.group("validation-loop")
def validation_loop_group() -> None:
    """Spec-first deterministic validation loop commands."""


@validation_loop_group.command("validate")
@click.option(
    "--spec",
    "-s",
    default="deployment_config",
    help="Preset name (deployment_config, plugin_manifest) or path to schema file",
)
@click.option("--data", "-d", default=None, help="Inline JSON payload string")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to JSON payload file",
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def validate_command(
    spec: str, data: str | None, file: Path | None, as_json: bool
) -> None:
    """Validate a structured JSON payload against a specification."""
    if data is None and file is None:
        click.secho("Error: Provide either --data '<json>' or --file <path>", fg="red")
        sys.exit(1)

    payload_raw = data if data is not None else file.read_text(encoding="utf-8")  # type: ignore
    try:
        payload = _json.loads(payload_raw)
    except Exception as exc:
        click.secho(f"Error parsing JSON payload: {exc}", fg="red")
        sys.exit(1)

    # If spec points to a file, read it
    spec_arg: str | dict[str, Any] = spec
    spec_path = Path(spec)
    if spec_path.exists() and spec_path.is_file():
        try:
            spec_arg = _json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception as exc:
            click.secho(f"Error reading schema file '{spec}': {exc}", fg="red")
            sys.exit(1)

    svc = get_validation_service()
    res = svc.validate(payload, spec_arg)

    if as_json:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        if not res.is_valid:
            sys.exit(1)
        return

    click.secho("=== Deterministic Validation Report ===", fg="cyan", bold=True)
    click.echo(f"Spec: {spec}")
    click.echo(f"Duration: {res.duration_ms:.3f} ms")
    if res.is_valid:
        click.secho("Status: PASSED (Valid)", fg="green", bold=True)
    else:
        click.secho("Status: FAILED (Invalid)", fg="red", bold=True)
        if res.tier_failures:
            click.echo(f"Tier Failures: {', '.join(res.tier_failures)}")
        click.secho("Errors:", fg="yellow")
        for err in res.errors:
            click.echo(f"  • {err}")
        sys.exit(1)


@validation_loop_group.command("run")
@click.option(
    "--request",
    "-r",
    required=True,
    help="Generation task request/objective",
)
@click.option(
    "--spec",
    "-s",
    default="deployment_config",
    help="Preset name (deployment_config, plugin_manifest) or schema file",
)
@click.option(
    "--attempts",
    "-a",
    default=3,
    type=int,
    help="Max retry ceiling before give-up triage (default 3)",
)
@click.option(
    "--simulate",
    type=click.Choice(["success", "retry_recovery", "fail_exhausted"]),
    default="retry_recovery",
    help="Simulation mode: success on turn 1, recovery on turn 2, or exhausted retries",
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def run_command(
    request: str, spec: str, attempts: int, simulate: str, as_json: bool
) -> None:
    """Run a deterministic validation loop with state machine execution."""
    svc = get_validation_service()

    def simulated_generator(
        req: str, errors: list[str], attempt: int
    ) -> dict[str, Any]:
        if simulate == "success" or (simulate == "retry_recovery" and attempt > 1):
            return {
                "service_name": "payments-api",
                "replicas": 3,
                "resources": {"cpu_limit": 1.0, "memory_limit_mb": 512},
                "health_check": {
                    "path": "/healthz",
                    "timeout_seconds": 2,
                    "interval_seconds": 10,
                },
            }
        # Failing attempt (Tier 3 violation)
        return {
            "service_name": "payments-api",
            "replicas": 8,
            "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
            "health_check": {
                "path": "/healthz",
                "timeout_seconds": 2,
                "interval_seconds": 10,
            },
        }

    res = svc.execute_loop(
        request, simulated_generator, spec=spec, max_attempts=attempts
    )

    if as_json:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.secho("=== Deterministic Validation Loop Execution ===", fg="cyan", bold=True)
    click.echo(f"Request: {request}")
    click.echo(f"Spec: {spec}")
    click.echo(f"Attempts: {res.attempts}/{attempts}")
    if res.status == "success":
        click.secho("Result: SUCCESS", fg="green", bold=True)
    else:
        click.secho("Result: REJECTED (HTTP 422 Fail-Closed)", fg="red", bold=True)
        if res.triage_record:
            click.echo(f"Triage Timestamp: {res.triage_record.timestamp}")
            click.echo(f"Residual Errors: {len(res.triage_record.final_errors)}")
            for err in res.triage_record.final_errors:
                click.echo(f"  • {err}")


@validation_loop_group.command("specs")
@click.option("--name", "-n", default=None, help="Inspect specific preset schema")
def specs_command(name: str | None) -> None:
    """List available validation specification presets."""
    svc = get_validation_service()
    if name:
        spec_data = svc.get_preset_spec(name)
        if spec_data is None:
            click.secho(f"Preset '{name}' not found.", fg="red")
            sys.exit(1)
        click.echo(_json.dumps(spec_data, indent=2))
        return

    presets = svc.list_presets()
    click.secho("Available Validation Specification Presets:", fg="cyan", bold=True)
    for p in presets:
        click.echo(f"  • {p}")


@validation_loop_group.command("brief")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output HTML file path",
)
@click.option(
    "--spec",
    "-s",
    default="deployment_config",
    help="Specification preset",
)
def brief_command(output: Path | None, spec: str) -> None:
    """Generate an interactive HTML visual brief for validation."""
    svc = get_validation_service()

    # Generate sample loop result
    def sample_gen(req: str, errors: list[str], attempt: int) -> dict[str, Any]:
        if attempt > 1:
            return {
                "service_name": "worker-pool",
                "replicas": 4,
                "resources": {"cpu_limit": 1.5, "memory_limit_mb": 1024},
                "health_check": {
                    "path": "/healthz",
                    "timeout_seconds": 2,
                    "interval_seconds": 15,
                },
            }
        return {
            "service_name": "worker-pool",
            "replicas": 10,
            "resources": {"cpu_limit": 0.5, "memory_limit_mb": 1024},
            "health_check": {
                "path": "/healthz",
                "timeout_seconds": 20,
                "interval_seconds": 10,
            },
        }

    loop_res = svc.execute_loop(
        "Deploy resilient worker pool", sample_gen, spec=spec, max_attempts=3
    )
    brief_path = svc.visual_brief(
        loop_res,
        title="Deterministic Validation Brief — Worker Pool",
        output_path=output,
    )
    click.secho("Interactive Visual Brief generated:", fg="green", bold=True)
    click.echo(f"  {brief_path.resolve()}")
