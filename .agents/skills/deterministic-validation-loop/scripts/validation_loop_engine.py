"""Deterministic Validation Loop Engine.

Spec-first 3-tier validation hierarchy, structured error delta injection,
and bounded retry triage for LLM structured outputs (Ramavat, 2026).
"""

from __future__ import annotations

import datetime
import json
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from jsonschema import ValidationError
from jsonschema import validate as json_validate


class ValidationTier(str, Enum):
    """Validation hierarchy tiers."""

    TIER_1_SCHEMA = (
        "tier_1_schema"  # Syntax, parseability, required fields, basic types
    )
    TIER_2_BOUNDS = "tier_2_bounds"  # Numerical ranges, regex patterns, resource limits
    TIER_3_INVARIANTS = "tier_3_invariants"  # Cross-field relational business rules


@dataclass(slots=True, frozen=True)
class ValidationRule:
    """A deterministic validation rule applied to structured payloads."""

    name: str
    tier: ValidationTier
    description: str
    predicate: Callable[[dict[str, Any]], tuple[bool, str | None]]

    def evaluate(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
        """Evaluate the predicate against a payload."""
        try:
            return self.predicate(payload)
        except Exception as exc:
            return False, f"Rule '{self.name}' crashed with: {exc}"


@dataclass(slots=True, frozen=True)
class ValidationReport:
    """Report produced by executing validation against a payload."""

    is_valid: bool
    errors: tuple[str, ...] = field(default_factory=tuple)
    tier_failures: tuple[ValidationTier, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0

    @property
    def error_count(self) -> int:
        """Total number of detected errors."""
        return len(self.errors)


@dataclass(slots=True, frozen=True)
class ValidationSpec:
    """Declarative specification encapsulating schema and tiered invariants."""

    name: str
    schema: dict[str, Any]
    rules: tuple[ValidationRule, ...] = field(default_factory=tuple)
    bail_early_on_tier_1: bool = True

    def validate(self, payload: dict[str, Any]) -> ValidationReport:
        """Execute 3-tier validation against payload."""
        start_time = time.perf_counter()
        errors: list[str] = []
        tier_failures: set[ValidationTier] = set()

        # Tier 1: Structural Schema Validation
        try:
            json_validate(instance=payload, schema=self.schema)
        except ValidationError as e:
            errors.append(f"Schema: {e.message} (at {list(e.path)})")
            tier_failures.add(ValidationTier.TIER_1_SCHEMA)
            if self.bail_early_on_tier_1:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return ValidationReport(
                    is_valid=False,
                    errors=tuple(errors),
                    tier_failures=tuple(sorted(tier_failures, key=lambda t: t.value)),
                    duration_ms=round(elapsed, 4),
                )

        # Tier 2 & Tier 3: Custom Invariant Rules
        for rule in self.rules:
            passed, err_msg = rule.evaluate(payload)
            if not passed and err_msg:
                errors.append(err_msg)
                tier_failures.add(rule.tier)

        elapsed = (time.perf_counter() - start_time) * 1000.0
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            tier_failures=tuple(sorted(tier_failures, key=lambda t: t.value)),
            duration_ms=round(elapsed, 4),
        )


@dataclass(slots=True, frozen=True)
class TriageRecord:
    """Audit record capturing failed state after retry ceiling exhaustion."""

    request: str
    final_errors: tuple[str, ...]
    attempts: int
    error_code: int = 422
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


@dataclass(slots=True, frozen=True)
class LoopExecutionResult:
    """Aggregate result from executing a deterministic validation state machine loop."""

    status: str  # "success" | "rejected"
    payload: dict[str, Any] | None
    attempts: int
    errors: tuple[str, ...] = field(default_factory=tuple)
    triage_record: TriageRecord | None = None
    trace: tuple[dict[str, Any], ...] = field(default_factory=tuple)


# --- Built-in Preset Specifications ---

DEPLOYMENT_CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["service_name", "replicas", "resources", "health_check"],
    "properties": {
        "service_name": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "replicas": {"type": "integer", "minimum": 1, "maximum": 20},
        "resources": {
            "type": "object",
            "required": ["cpu_limit", "memory_limit_mb"],
            "properties": {
                "cpu_limit": {"type": "number", "minimum": 0.1, "maximum": 8.0},
                "memory_limit_mb": {
                    "type": "integer",
                    "minimum": 128,
                    "maximum": 16384,
                },
            },
        },
        "health_check": {
            "type": "object",
            "required": ["path", "timeout_seconds", "interval_seconds"],
            "properties": {
                "path": {"type": "string", "pattern": "^/"},
                "timeout_seconds": {"type": "integer", "minimum": 1},
                "interval_seconds": {"type": "integer", "minimum": 5},
            },
        },
    },
}


def _check_replica_cpu(cfg: dict[str, Any]) -> tuple[bool, str | None]:
    replicas = cfg.get("replicas")
    resources = cfg.get("resources")
    if (
        isinstance(replicas, int)
        and isinstance(resources, dict)
        and replicas > 5
        and resources.get("cpu_limit", 0) < 1.0
    ):
        return False, f"replicas={replicas} requires cpu_limit >= 1.0"
    return True, None


def _check_health_timeout(cfg: dict[str, Any]) -> tuple[bool, str | None]:
    hc = cfg.get("health_check")
    if isinstance(hc, dict):
        timeout = hc.get("timeout_seconds")
        interval = hc.get("interval_seconds")
        if (
            isinstance(timeout, (int, float))
            and isinstance(interval, (int, float))
            and timeout >= interval
        ):
            return False, "timeout_seconds must be < interval_seconds"
    return True, None


DEPLOYMENT_CONFIG_SPEC = ValidationSpec(
    name="deployment_config",
    schema=DEPLOYMENT_CONFIG_SCHEMA,
    rules=(
        ValidationRule(
            name="replica_cpu_bound",
            tier=ValidationTier.TIER_3_INVARIANTS,
            description="Replicas > 5 require cpu_limit >= 1.0",
            predicate=_check_replica_cpu,
        ),
        ValidationRule(
            name="health_check_interval_bound",
            tier=ValidationTier.TIER_3_INVARIANTS,
            description="Health timeout_seconds must be less than interval_seconds",
            predicate=_check_health_timeout,
        ),
    ),
    bail_early_on_tier_1=True,
)

PLUGIN_MANIFEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name", "version", "category", "description", "provides"],
    "properties": {
        "name": {"type": "string", "pattern": "^[a-z0-9_]+$"},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "category": {"type": "string", "minLength": 3},
        "description": {"type": "string", "minLength": 10},
        "provides": {"type": "array", "items": {"type": "string"}},
        "requires": {"type": "array", "items": {"type": "string"}},
    },
}

PLUGIN_MANIFEST_SPEC = ValidationSpec(
    name="plugin_manifest",
    schema=PLUGIN_MANIFEST_SCHEMA,
    rules=(),
    bail_early_on_tier_1=True,
)


class DeterministicValidationEngine:
    """Engine executing spec-first 3-tier validation loops with delta injection and bounded retry triage."""

    def __init__(self) -> None:
        self._presets: dict[str, ValidationSpec] = {
            "deployment_config": DEPLOYMENT_CONFIG_SPEC,
            "plugin_manifest": PLUGIN_MANIFEST_SPEC,
        }

    def register_preset(self, spec: ValidationSpec) -> None:
        """Register a custom validation specification preset."""
        self._presets[spec.name] = spec

    def get_preset(self, name: str) -> ValidationSpec | None:
        """Retrieve a registered preset specification by name."""
        return self._presets.get(name)

    def list_presets(self) -> list[str]:
        """List all available preset specification names."""
        return sorted(self._presets.keys())

    def validate(
        self, spec: ValidationSpec, payload: dict[str, Any]
    ) -> ValidationReport:
        """Validate a payload against a specification."""
        return spec.validate(payload)

    def format_error_feedback(self, request: str, errors: Sequence[str]) -> str:
        """Format unambiguous error strings for LLM delta injection (Ramavat 2026)."""
        content = f"Generate configuration for: {request}"
        if errors:
            content += "\n\nYour previous attempt had these errors:\n"
            content += "\n".join(f"- {err}" for err in errors)
            content += "\nFix ALL of them."
        return content

    def run_loop(
        self,
        request: str,
        generator_func: Callable[[str, list[str], int], dict[str, Any] | None | str],
        spec: ValidationSpec,
        max_attempts: int = 3,
    ) -> LoopExecutionResult:
        """Execute the cyclic state graph: generate -> validate -> feedback -> triage."""
        attempts = 0
        errors: list[str] = []
        payload: dict[str, Any] | None = None
        trace: list[dict[str, Any]] = []

        while attempts < max_attempts:
            attempts += 1
            raw_output = generator_func(request, errors, attempts)

            # Handle JSON string output
            if isinstance(raw_output, str):
                try:
                    payload = json.loads(raw_output)
                except Exception:
                    payload = None
            else:
                payload = raw_output

            if not payload or not isinstance(payload, dict):
                errors = ["Output was not valid JSON or was empty"]
                trace.append(
                    {
                        "attempt": attempts,
                        "status": "syntax_error",
                        "errors": list(errors),
                        "payload": None,
                    }
                )
                continue

            report = spec.validate(payload)
            if report.is_valid:
                trace.append(
                    {
                        "attempt": attempts,
                        "status": "success",
                        "errors": [],
                        "payload": payload,
                        "duration_ms": report.duration_ms,
                    }
                )
                return LoopExecutionResult(
                    status="success",
                    payload=payload,
                    attempts=attempts,
                    errors=(),
                    triage_record=None,
                    trace=tuple(trace),
                )

            errors = list(report.errors)
            trace.append(
                {
                    "attempt": attempts,
                    "status": "validation_failed",
                    "errors": list(errors),
                    "payload": payload,
                    "tier_failures": [t.value for t in report.tier_failures],
                    "duration_ms": report.duration_ms,
                }
            )

        # Retries exhausted -> Execute Triage (Fail Closed HTTP 422)
        triage = TriageRecord(
            request=request,
            final_errors=tuple(errors),
            attempts=attempts,
            error_code=422,
        )

        return LoopExecutionResult(
            status="rejected",
            payload=payload,
            attempts=attempts,
            errors=tuple(errors),
            triage_record=triage,
            trace=tuple(trace),
        )

    def generate_visual_brief(
        self,
        result: LoopExecutionResult | ValidationReport,
        title: str = "Deterministic Validation Brief",
        output_path: str | Path | None = None,
    ) -> Path:
        """Synthesize an interactive HTML visual brief illustrating the execution trace."""
        if output_path is None:
            ts = int(time.time())
            output_path = Path(tempfile.gettempdir()) / f"validation-brief-{ts}.html"
        else:
            output_path = Path(output_path)

        is_loop = hasattr(result, "status")
        is_success = (
            (result.status == "success")
            if is_loop
            else getattr(result, "is_valid", False)
        )
        status_color = "emerald" if is_success else "rose"
        status_text = "PASSED" if is_success else "REJECTED"

        trace_rows = ""
        if is_loop and result.trace:
            for item in result.trace:
                att = item["attempt"]
                st = item["status"]
                errs = (
                    "<br>".join(f"&bull; {e}" for e in item.get("errors", []))
                    or "<span class='text-emerald-400'>None</span>"
                )
                row_bg = "bg-slate-900/50" if att % 2 == 0 else "bg-slate-900/80"
                badge = (
                    "<span class='px-2 py-0.5 rounded text-xs bg-emerald-950 text-emerald-300 border border-emerald-800'>Success</span>"
                    if st == "success"
                    else "<span class='px-2 py-0.5 rounded text-xs bg-rose-950 text-rose-300 border border-rose-800'>Failed</span>"
                )
                trace_rows += f"""
                <tr class="{row_bg} border-b border-slate-800">
                  <td class="p-3 font-mono text-center text-slate-300">{att}</td>
                  <td class="p-3">{badge}</td>
                  <td class="p-3 text-xs font-mono text-slate-300">{errs}</td>
                </tr>
                """

        html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Inter', sans-serif; }}
    code, pre {{ font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-6 md:p-12">
  <div class="max-w-4xl mx-auto space-y-8">
    <header class="border-b border-slate-800 pb-6 flex justify-between items-center">
      <div>
        <span class="text-xs uppercase tracking-wider text-cyan-400 font-semibold">Deterministic Validation Loop</span>
        <h1 class="text-2xl font-bold mt-1 text-white">{title}</h1>
      </div>
      <div class="px-3 py-1 rounded-full text-xs font-bold bg-{status_color}-950 text-{status_color}-400 border border-{status_color}-800">
        {status_text}
      </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div class="text-xs text-slate-400">Total Attempts</div>
        <div class="text-2xl font-bold font-mono text-slate-100 mt-1">{result.attempts if is_loop else 1}</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div class="text-xs text-slate-400">Active Errors</div>
        <div class="text-2xl font-bold font-mono text-rose-400 mt-1">{len(result.errors)}</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div class="text-xs text-slate-400">Triage Status</div>
        <div class="text-sm font-semibold text-slate-200 mt-2">{f"HTTP {result.triage_record.error_code} Logged" if is_loop and result.triage_record else "None (Passed)"}</div>
      </div>
    </div>

    {"<div class='bg-slate-900 border border-slate-800 rounded-xl overflow-hidden'><table class='w-full text-left text-sm'><thead class='bg-slate-950 text-slate-400 border-b border-slate-800'><tr><th class='p-3 text-center w-20'>Attempt</th><th class='p-3 w-32'>Status</th><th class='p-3'>Delta Feedback / Errors</th></tr></thead><tbody>" + trace_rows + "</tbody></table></div>" if trace_rows else ""}

    <footer class="pt-6 border-t border-slate-800 text-xs text-slate-500 text-center">
      Deterministic Validation Loop &bull; Spec-First Architecture (Ramavat 2026) &bull; Brain Harness
    </footer>
  </div>
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")
        return output_path
