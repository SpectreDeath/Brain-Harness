"""HarnessCompass service protocol, typed models, and ServiceKey.

Elevates the HarnessCompass automatic harness discovery, calibration & R3 integration engine
(Zhang et al., arXiv:2608.01918v1, 2026, ki-harnesscompass-evolution) into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class GateViolationData(BaseModel):
    """Data transfer model for an individual Generalization Gate violation."""

    surface: str = Field(..., description="Target component surface (e.g. middleware, systemprompt)")
    rule: str = Field(..., description="Violated rule identifier (e.g. BANNED_TASK_INSTANCE_ID)")
    detail: str = Field(..., description="Human-readable violation details")


class GateResultData(BaseModel):
    """Data transfer model for Generalization Gate evaluation outcome."""

    passed: bool = Field(..., description="Whether the edit satisfies both Content and Placement invariants")
    violations: list[GateViolationData] = Field(default_factory=list, description="List of detected violations")


class HarnessEditData(BaseModel):
    """Data transfer model for a candidate harness modification."""

    id: str = Field(..., description="Unique edit identifier (e.g. chg-01)")
    surface: str = Field(..., description="Harness component surface")
    description: str = Field(..., description="Semantic purpose of the edit")
    target_file: str = Field(..., description="Relative destination file path")
    content: str = Field(..., description="Code or guidance text content")
    action_type: str = Field(default="improvement", description="Action type: new, improvement, rollback")
    is_advisory: bool = Field(default=False, description="Whether the change is behavioral advice/guidance")
    is_code_executable: bool = Field(default=False, description="Whether the change is deterministic executable code")


class FeedbackItemData(BaseModel):
    """Data transfer model for first-person agent feedback."""

    kind: str = Field(..., description="Feedback kind: improve_existing or new_capability")
    component: str = Field(..., description="Harness component surface associated with friction")
    friction: str = Field(..., description="Description of experienced friction or limitation")
    desired_change: str = Field(..., description="Proposed modification or desired tool capability")
    trace_refs: list[str] = Field(default_factory=list, description="Referenced turn identifiers from raw trace")
    severity: int = Field(default=1, description="Subjective severity level (1-5)")
    attribution: str = Field(default="harness", description="Attribution: harness, agent_reasoning, task_ambiguity, environment")
    self_consistency: str = Field(default="pre_post_agree", description="Reconciliation status: pre_post_agree, partial, conflict")


class GroundedEvidenceData(BaseModel):
    """Data transfer model for trace-grounded feedback verification."""

    item: FeedbackItemData = Field(..., description="Original agent feedback item")
    grounded: bool = Field(..., description="Whether the feedback item is grounded in trace evidence")
    assigned_track: str = Field(..., description="Assigned optimization track: structural or guidance")
    confidence: float = Field(..., description="Calculated confidence score (0.0 to 1.0)")
    rejection_reason: str = Field(default="", description="Reason for rejection if not grounded")


class IntegrationManifestData(BaseModel):
    """Data transfer model for R3 integration synthesis results."""

    base_winner: str = Field(..., description="Winning track variant name")
    winner_score: float = Field(..., description="Winning track evaluation Pass@1 score")
    loser_score: float = Field(..., description="Losing track evaluation Pass@1 score")
    kept_from_loser: list[dict[str, str]] = Field(default_factory=list, description="Edits retained from losing track during Revision")
    dropped_from_loser: list[dict[str, str]] = Field(default_factory=list, description="Edits discarded from losing track")
    removed_as_redundant: list[dict[str, str]] = Field(default_factory=list, description="Advisory edits purged by Occam's Razor Refinement")


class EvolutionRoundData(BaseModel):
    """Data transfer model for a complete simulated evolution round."""

    round_num: int = Field(..., description="Evolution round index (1 to N)")
    baseline_score: float = Field(..., description="Starting baseline Pass@1 score")
    structural_score: float = Field(..., description="Track A (Structural) Pass@1 score")
    guidance_score: float = Field(..., description="Track B (Guidance) Pass@1 score")
    winner_track: str = Field(..., description="Designated winning track (structural or guidance)")
    winner_score: float = Field(..., description="Highest achieving track score")
    manifest: IntegrationManifestData = Field(..., description="R3 Integration synthesis manifest")
    accepted: bool = Field(..., description="Whether consolidated harness was accepted over baseline")
    notes: str = Field(default="", description="Diagnostic evaluation notes")


@runtime_checkable
class HarnessCompassService(Protocol):
    """Protocol for autonomous harness evolution, generalization gating, and R3 integration."""

    def validate_edit(self, edit: HarnessEditData) -> GateResultData:
        """Evaluate a candidate harness edit against Content and Placement invariants."""
        ...

    def ground_feedback(
        self, item: FeedbackItemData, trajectory_turns: Sequence[dict[str, Any]]
    ) -> GroundedEvidenceData:
        """Ground first-person agent feedback against raw trajectory turns."""
        ...

    def execute_r3_merge(
        self,
        winner_name: str,
        winner_score: float,
        winner_edits: Sequence[HarnessEditData],
        loser_name: str,
        loser_score: float,
        loser_edits: Sequence[HarnessEditData],
    ) -> IntegrationManifestData:
        """Execute R3 integration: Revision, Recombination, and Occam's Razor Refinement."""
        ...

    def simulate_round(
        self,
        round_num: int,
        baseline_score: float,
        structural_edits: Sequence[HarnessEditData],
        guidance_edits: Sequence[HarnessEditData],
        structural_score: float,
        guidance_score: float,
    ) -> EvolutionRoundData:
        """Simulate a full 5-stage closed loop evolution and acceptance round."""
        ...

    def generate_visual_brief(
        self, output_path: str | Path | None = None
    ) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and Mermaid DAG."""
        ...


HARNESS_COMPASS_SERVICE_KEY: ServiceKey[HarnessCompassService] = ServiceKey(
    "service.harness_compass"
)
