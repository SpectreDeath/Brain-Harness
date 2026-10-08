"""Endogenous Memory & Reflection Engine for Brain Harness.

Harvests internal history (HTML architecture visual briefs, conversation transcripts,
walkthroughs, and execution logs), reconstructs episodic memory trajectories, and
distills actionable, Isnad-grounded Knowledge Items (KIs) into the Knowledge Vault.
"""

from __future__ import annotations

from harness.creator.reflection.distiller import EpisodicMemoryReflector
from harness.creator.reflection.engine import (
    HARNESS_REFLECTOR_ENGINE_KEY,
    HarnessReflectorEngine,
    resolve_reflector_engine,
)
from harness.creator.reflection.extractors import (
    ArchitectureSeamPatternExtractor,
    BaseMemoryPatternExtractor,
    ComputeCalibrationPatternExtractor,
    ErrorRecoveryPatternExtractor,
    MemoryPatternPipeline,
    TestExecutionPatternExtractor,
    TransactionalStepPatternExtractor,
)
from harness.creator.reflection.harvester import HarnessHistoryHarvester
from harness.creator.reflection.models import (
    DistilledHeuristic,
    ReflectionReport,
    ReflectionScope,
    ReportArtifact,
    TranscriptSession,
)
from harness.creator.reflection.visualizer import generate_reflection_html_brief

__all__ = [
    "ArchitectureSeamPatternExtractor",
    "BaseMemoryPatternExtractor",
    "ComputeCalibrationPatternExtractor",
    "DistilledHeuristic",
    "EpisodicMemoryReflector",
    "ErrorRecoveryPatternExtractor",
    "HARNESS_REFLECTOR_ENGINE_KEY",
    "HarnessHistoryHarvester",
    "HarnessReflectorEngine",
    "MemoryPatternPipeline",
    "ReflectionReport",
    "ReflectionScope",
    "ReportArtifact",
    "TestExecutionPatternExtractor",
    "TransactionalStepPatternExtractor",
    "TranscriptSession",
    "generate_reflection_html_brief",
    "resolve_reflector_engine",
]
