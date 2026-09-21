"""DeterministicValidation service protocol, typed models, and ServiceKey.

Elevates the spec-first deterministic validation loop (Ramavat 2026)
into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ValidationResultData(BaseModel):
    """Validation report payload."""

    is_valid: bool = Field(..., description="Whether validation passed cleanly")
    errors: list[str] = Field(
        default_factory=list, description="List of actionable error strings"
    )
    tier_failures: list[str] = Field(
        default_factory=list,
        description="Failing validation tiers (tier_1_schema, tier_2_bounds, tier_3_invariants)",
    )
    duration_ms: float = Field(
        default=0.0, description="Validation execution time in milliseconds"
    )


class TriageRecordData(BaseModel):
    """Audit record capturing failed state after retry ceiling exhaustion."""

    request: str = Field(..., description="Original generation request")
    final_errors: list[str] = Field(
        default_factory=list, description="Final error list on failure"
    )
    attempts: int = Field(..., description="Total attempts executed")
    error_code: int = Field(default=422, description="HTTP rejection error code")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        description="ISO UTC timestamp",
    )


class LoopExecutionResultData(BaseModel):
    """Result of state machine validation loop."""

    status: str = Field(..., description="success | rejected")
    payload: dict[str, Any] | None = Field(
        default=None, description="Final validated payload if successful"
    )
    attempts: int = Field(..., description="Attempts taken before completion")
    errors: list[str] = Field(
        default_factory=list, description="Residual errors if rejected"
    )
    triage_record: TriageRecordData | None = Field(
        default=None, description="Triage audit record if rejected"
    )
    trace: list[dict[str, Any]] = Field(
        default_factory=list, description="Step-by-step loop execution trace"
    )


@runtime_checkable
class DeterministicValidationService(Protocol):
    """Protocol for spec-first 3-tier deterministic validation loops."""

    def validate(
        self,
        payload: dict[str, Any],
        spec: str | dict[str, Any],
    ) -> ValidationResultData:
        """Validate a payload against a preset name or spec schema."""
        ...

    def execute_loop(
        self,
        request: str,
        generator: Any,
        spec: str | dict[str, Any],
        max_attempts: int = 3,
    ) -> LoopExecutionResultData:
        """Execute state machine loop with delta error injection and bounded budget."""
        ...

    def format_feedback(self, request: str, errors: list[str]) -> str:
        """Format unambiguous error strings for LLM delta injection."""
        ...

    def get_preset_spec(self, name: str) -> dict[str, Any] | None:
        """Retrieve schema dictionary for a built-in preset."""
        ...

    def list_presets(self) -> list[str]:
        """List registered preset specification names."""
        ...

    def visual_brief(
        self,
        result: Any,
        title: str = "Deterministic Validation Brief",
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief with execution trace."""
        ...


DETERMINISTIC_VALIDATION_SERVICE_KEY: ServiceKey[DeterministicValidationService] = (
    ServiceKey("service.deterministic_validation")
)
