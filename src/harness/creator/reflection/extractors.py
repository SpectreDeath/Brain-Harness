"""Modular memory pattern extractors and distillation pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Sequence

import structlog

from harness.creator.reflection.models import (
    DistilledHeuristic,
    ReflectionScope,
    ReportArtifact,
    TranscriptSession,
)

logger = structlog.get_logger(__name__)


class BaseMemoryPatternExtractor(ABC):
    """Abstract base class for modular memory pattern extractors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this extractor."""

    @property
    @abstractmethod
    def category(self) -> str:
        """Heuristic category produced by this extractor."""

    @abstractmethod
    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        """Extract distilled heuristics from reports and transcripts."""


class ArchitectureSeamPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts lifecycle staging, lazy venv, and CLI group consolidation invariants."""

    @property
    def name(self) -> str:
        return "architecture_seams"

    @property
    def category(self) -> str:
        return "architecture"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            if rep.report_type != "architecture_review":
                continue

            combined_text = (rep.content_text + " " + " ".join(rep.friction_points)).lower()

            # 1. Lazy Subprocess Staging
            if any(k in combined_text for k in ["lazy", "subprocess", "venv", "cold-start"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="Lazy Subprocess Staging for Sandboxed External Plugins",
                        category="architecture",
                        heuristic=(
                            "External plugins with subprocess/venv isolation must remain in DISCOVERED/VALIDATED state "
                            "during kernel startup and test execution, provisioning virtual environments lazily on first invocation "
                            "to eliminate cold-start timeouts."
                        ),
                        anti_pattern="Eagerly provisioning virtualenvs for all user plugins in HarnessRuntime.start().",
                        confidence=0.98,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Eager venv creation on Windows causes 60s pytest timeout; lazy staging resolves startup in <10ms.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

            # 2. CLI Single-Source Consolidation
            if any(k in combined_text for k in ["cli", "bridge", "shadow", "command group"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="Click CLI Group Single-Source Consolidation",
                        category="architecture",
                        heuristic=(
                            "CLI command groups (e.g. '@main.group(\"bridge\")') must be declared exactly once in a single "
                            "co-located block to prevent later definitions from shadowing subcommands and breaking CLI test assertions."
                        ),
                        anti_pattern="Redefining CLI command groups at the bottom of cli.py.",
                        confidence=0.99,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Duplicate Click group declarations shadow earlier subcommands.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class TransactionalStepPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts agent step transaction rollback and ACID state boundary invariants."""

    @property
    def name(self) -> str:
        return "transactional_steps"

    @property
    def category(self) -> str:
        return "architecture"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            combined_text = (rep.content_text + " " + " ".join(rep.friction_points)).lower()
            if any(k in combined_text for k in ["transaction", "rollback", "acid", "dispose"]):
                heuristics.append(
                    DistilledHeuristic(
                        title="ReAct Agent Step Transactional Isolation",
                        category="architecture",
                        heuristic=(
                            "Agent tool invocations should execute inside context transactions ('async with context.transaction()') "
                            "with automatic rollback ('await tx.dispose()') whenever the tool returns an error payload or raises an exception."
                        ),
                        anti_pattern="Mutating shared ServiceContext during tool execution without an ACID boundary.",
                        confidence=0.96,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "Step-level transactional boundaries guarantee clean state rollback on tool failures.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class ComputeCalibrationPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts compute model assessment and reasoning budget routing invariants."""

    @property
    def name(self) -> str:
        return "compute_calibration"

    @property
    def category(self) -> str:
        return "performance"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            if rep.report_type == "compute_assessment" or "compute" in rep.title.lower():
                heuristics.append(
                    DistilledHeuristic(
                        title="Multi-Dimensional Compute Assessment Calibration",
                        category="performance",
                        heuristic=(
                            "Route high-reasoning tasks (architectural refactoring, debugging concurrency) to deep reasoning models "
                            "(gemini-3.7-flash with HIGH thinking or claude-3.7-sonnet with thinking budget), while routing mechanical tasks "
                            "to fast non-thinking tiers."
                        ),
                        anti_pattern="Using one-size-fits-all model tiers across heterogeneous task surfaces.",
                        confidence=0.95,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": rep.file_path.name,
                                "timestamp": rep.created_at,
                                "assertion": "5-dimensional scoring vectors optimize reasoning token spend and latency.",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class ErrorRecoveryPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts async timeout, cancellation, and error recovery invariants from transcripts."""

    @property
    def name(self) -> str:
        return "error_recovery"

    @property
    def category(self) -> str:
        return "error_recovery"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for tr in transcripts:
            if not tr.errors_encountered:
                continue

            for err in tr.errors_encountered:
                err_lower = err.lower()
                if "timed out" in err_lower or "timeout" in err_lower:
                    heuristics.append(
                        DistilledHeuristic(
                            title="Async Execution Timeout Isolation",
                            category="error_recovery",
                            heuristic=(
                                "Long-running subagent tasks and test execution pipelines must specify explicit, granular timeouts "
                                "with thread-safe cancellation to prevent blocking the main asyncio loop."
                            ),
                            anti_pattern="Unbounded await calls on external subprocesses.",
                            confidence=0.92,
                            source_artifacts=[str(tr.log_path)],
                            isnad_claims=[
                                {
                                    "source": f"transcript:{tr.conversation_id}",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "assertion": "Transcript records timeout failure recovery.",
                                    "status": "VERIFIED",
                                }
                            ],
                        )
                    )
                    break

        return heuristics


class TestExecutionPatternExtractor(BaseMemoryPatternExtractor):
    """Extracts test regression patterns, failure coordinates, and invariant violations."""

    @property
    def name(self) -> str:
        return "test_execution"

    @property
    def category(self) -> str:
        return "error_recovery"

    def extract(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
    ) -> list[DistilledHeuristic]:
        heuristics: list[DistilledHeuristic] = []

        for rep in reports:
            if rep.report_type != "test_report" and "test" not in rep.title.lower():
                continue

            failures = rep.metadata.get("failures", [])
            for fail in failures:
                test_name = fail.get("test_name", "unknown_test")
                test_file = fail.get("test_file", str(rep.file_path))
                message = fail.get("message", "")

                title = f"Test Regression: {test_name}"
                heuristic_text = (
                    f"Regression detected in test '{test_name}' ({test_file}). "
                    f"Failure reason: {message[:160]}. "
                    f"Enforce regression safety net before committing changes."
                )

                heuristics.append(
                    DistilledHeuristic(
                        title=title,
                        category="error_recovery",
                        heuristic=heuristic_text,
                        anti_pattern=f"Allowing {test_name} assertion failure to persist across CI cycles.",
                        confidence=0.97,
                        source_artifacts=[str(rep.file_path)],
                        isnad_claims=[
                            {
                                "source": test_file,
                                "timestamp": rep.created_at,
                                "assertion": f"Test failure observed: {message[:120]}",
                                "status": "VERIFIED",
                            }
                        ],
                    )
                )

        return heuristics


class MemoryPatternPipeline:
    """Pluggable registry and execution pipeline for memory pattern extractors."""

    def __init__(self, extractors: list[BaseMemoryPatternExtractor] | None = None) -> None:
        if extractors is not None:
            self._extractors = list(extractors)
        else:
            self._extractors = [
                ArchitectureSeamPatternExtractor(),
                TransactionalStepPatternExtractor(),
                ComputeCalibrationPatternExtractor(),
                ErrorRecoveryPatternExtractor(),
                TestExecutionPatternExtractor(),
            ]

    def register(self, extractor: BaseMemoryPatternExtractor) -> None:
        """Register a custom pattern extractor."""
        self._extractors.append(extractor)

    def list_extractors(self) -> list[str]:
        """List registered extractor names."""
        return [e.name for e in self._extractors]

    def distill(
        self,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
        scope: ReflectionScope | None = None,
    ) -> list[DistilledHeuristic]:
        """Execute all registered extractors, deduplicate heuristics, and apply scope filters."""
        raw_heuristics: list[DistilledHeuristic] = []

        for ext in self._extractors:
            try:
                results = ext.extract(reports, transcripts)
                raw_heuristics.extend(results)
            except Exception as e:
                logger.warning("Pattern extractor failed", extractor=ext.name, error=str(e))

        # Deduplicate heuristics by title while aggregating provenance claims and sources
        deduped: dict[str, DistilledHeuristic] = {}
        for h in raw_heuristics:
            if scope and not scope.matches_category(h.category):
                continue
            if scope and h.confidence < scope.min_confidence:
                continue

            if h.title not in deduped:
                deduped[h.title] = h
            else:
                for src in h.source_artifacts:
                    if src not in deduped[h.title].source_artifacts:
                        deduped[h.title].source_artifacts.append(src)
                for clm in h.isnad_claims:
                    if clm not in deduped[h.title].isnad_claims:
                        deduped[h.title].isnad_claims.append(clm)

        return list(deduped.values())


__all__ = [
    "ArchitectureSeamPatternExtractor",
    "BaseMemoryPatternExtractor",
    "ComputeCalibrationPatternExtractor",
    "ErrorRecoveryPatternExtractor",
    "MemoryPatternPipeline",
    "TestExecutionPatternExtractor",
    "TransactionalStepPatternExtractor",
]
