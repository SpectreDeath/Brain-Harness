"""Data models for Media Mind Forge cognitive analysis and distillation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class MentalModel(BaseModel):
    """Ground-truth conceptual model or first principle extracted from media."""

    name: str = Field(..., description="Name of the mental model or philosophical concept")
    core_concept: str = Field(..., description="Core thesis and foundational premise")
    first_principles: list[str] = Field(default_factory=list, description="Underlying first-principle axioms")
    boundary_conditions: list[str] = Field(default_factory=list, description="Scope boundaries and applicability constraints")
    timestamp_start_s: float = Field(default=0.0, description="Start time offset in seconds")
    timestamp_end_s: float = Field(default=0.0, description="End time offset in seconds")
    source_quote: str = Field(default="", description="Representative verbatim quote from transcript")


class DecisionHeuristic(BaseModel):
    """Operational rule of thumb or decision tradeoff extracted from media."""

    name: str = Field(..., description="Heuristic name (e.g. Gruber's Minimal Commitment)")
    rule: str = Field(..., description="Actionable normative rule to apply")
    trade_off: str = Field(..., description="Trade-off balancing competing objectives")
    evaluation_criteria: list[str] = Field(default_factory=list, description="Checkable criteria satisfying this heuristic")
    source_quote: str = Field(default="", description="Supporting transcript excerpt")
    rule_type: str = Field(default="heuristic", description="Categorization: heuristic, validation, selection, invariant")
    isnad_claims: list[dict[str, Any]] = Field(default_factory=list, description="Timestamped source claims")


class DiagnosticQuestion(BaseModel):
    """Author's diagnostic coaching probe to evaluate work against domain standards."""

    question: str = Field(..., description="Diagnostic interrogation question")
    rationale: str = Field(..., description="Why this probe matters according to the author")
    passing_criteria: str = Field(..., description="What constitutes an exemplary or passing response")
    failing_indicators: list[str] = Field(default_factory=list, description="Telltale red flags indicating failure")


class ProceduralStage(BaseModel):
    """Concrete Shu-Ha-Ri execution stage with verifiable completion gate."""

    stage_num: int = Field(..., description="Sequential step number (1-based)")
    name: str = Field(..., description="Stage title (e.g. Competency Question Formulation)")
    objective: str = Field(..., description="Core objective accomplished in this stage")
    completion_criterion: str = Field(..., description="Deterministic completion gate distinguishing done from not-done")
    action_steps: list[str] = Field(default_factory=list, description="Concrete operational instructions")
    completion_gate: str = Field(default="", description="Alias for completion_criterion")

    def model_post_init(self, __context: Any) -> None:
        if not self.completion_gate and self.completion_criterion:
            self.completion_gate = self.completion_criterion
        elif not self.completion_criterion and self.completion_gate:
            self.completion_criterion = self.completion_gate


class AntiPatternItem(BaseModel):
    """Named failure mode paired with an invariant behavioral defense."""

    name: str = Field(..., description="Name of the anti-pattern (e.g. Over-Commitment)")
    telltale_symptom: str = Field(..., description="Observable symptom indicating occurrence")
    positive_rule: str = Field(..., description="Actionable invariant defense to enforce")
    risk_level: str = Field(default="HIGH", description="Risk level: HIGH, MEDIUM, CRITICAL")


class DistilledKnowledgeItem(BaseModel):
    """Ground-truth Knowledge Item (KI) formatted for the Harness Knowledge Vault."""

    id: str = Field(..., description="Canonical KI identifier (e.g. ki_media_ontological_engineering)")
    title: str = Field(..., description="Actionable heuristic title")
    summary: str = Field(..., description="Detailed operational synthesis and guidelines")
    source_target: str = Field(..., description="Source video URL, ID, or transcript file path")
    detected_format: str = Field(default="video_transcript", description="Source format signature")
    source_type: str = Field(default="video_transcript", description="Source taxonomy type")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    isnad_claims: list[dict[str, Any]] = Field(default_factory=list, description="Epistemic chain-of-custody claims")
    isnad_lineage: list[dict[str, Any]] = Field(default_factory=list, description="Alias for isnad_claims")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if not self.isnad_lineage and self.isnad_claims:
            self.isnad_lineage = self.isnad_claims
        elif not self.isnad_claims and self.isnad_lineage:
            self.isnad_claims = self.isnad_lineage


class CognitiveAnalysisReport(BaseModel):
    """Consolidated dual-lens cognitive analysis payload."""

    status: str = Field(default="ok", description="Execution outcome: ok or error")
    target_title: str = Field(default="Untitled Media", description="Title or subject of the analyzed media")
    skill_name: str = Field(default="ontological-engineering-coach", description="Normalized kebab-case skill identifier")
    video_id: str = Field(default="", description="11-character YouTube video ID if applicable")
    speaker: str = Field(default="Unknown", description="Identified speaker or presenter")
    author_or_speaker: str = Field(default="", description="Alias for speaker")
    total_duration_s: float = Field(default=0.0, description="Total video or audio duration in seconds")
    duration_seconds: float = Field(default=0.0, description="Alias for total_duration_s")
    word_count: int = Field(default=0, description="Total words analyzed")
    words_per_minute: float = Field(default=0.0, description="Calculated speaking pace")
    mental_models: list[MentalModel] = Field(default_factory=list, description="Epistemic mental models")
    decision_heuristics: list[DecisionHeuristic] = Field(default_factory=list, description="Operational heuristics")
    diagnostic_rubric: list[DiagnosticQuestion] = Field(default_factory=list, description="Diagnostic coaching scorecards")
    diagnostic_questions: list[DiagnosticQuestion] = Field(default_factory=list, description="Alias for diagnostic_rubric")
    procedural_stages: list[ProceduralStage] = Field(default_factory=list, description="Synthesized Shu-Ha-Ri execution stages")
    anti_patterns: list[AntiPatternItem] = Field(default_factory=list, description="Explicit failure modes and mitigations")
    knowledge_items: list[DistilledKnowledgeItem] = Field(default_factory=list, description="Generated Knowledge Items")
    visual_brief_path: str = Field(default="", description="Path to generated interactive HTML report in %TEMP%")

    def model_post_init(self, __context: Any) -> None:
        if not self.duration_seconds and self.total_duration_s:
            self.duration_seconds = self.total_duration_s
        elif not self.total_duration_s and self.duration_seconds:
            self.total_duration_s = self.duration_seconds

        if not self.author_or_speaker and self.speaker:
            self.author_or_speaker = self.speaker
        elif not self.speaker and self.author_or_speaker:
            self.speaker = self.author_or_speaker

        if not self.diagnostic_questions and self.diagnostic_rubric:
            self.diagnostic_questions = self.diagnostic_rubric
        elif not self.diagnostic_rubric and self.diagnostic_questions:
            self.diagnostic_rubric = self.diagnostic_questions
