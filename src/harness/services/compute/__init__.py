"""Compute & Model Assessor Subsystem.

Provides multi-dimensional complexity scoring, reasoning budget calibration,
pluggable provider parameter synthesis (Gemini, Claude, OpenAI, DeepSeek, Ollama, LiteLLM),
token economics & latency estimation, and interactive visual review brief generation.
"""

from __future__ import annotations

from harness.services.compute.brief import ComputeVisualBriefGenerator
from harness.services.compute.escalator import (
    DynamicTrajectoryEscalator,
    TrajectoryState,
)
from harness.services.compute.providers import (
    BaseProviderAdapter,
    ClaudeProviderAdapter,
    DeepSeekProviderAdapter,
    FallbackLiteLLMAdapter,
    GeminiProviderAdapter,
    OllamaProviderAdapter,
    OpenAIProviderAdapter,
    ProviderReasoningAdapter,
    ProviderReasoningRegistry,
)
from harness.services.compute.scorer import DimensionalScorer
from harness.services.compute.service import (
    COMPUTE_ASSESSOR_SERVICE,
    ComputeAssessorPlugin,
    ComputeAssessorService,
    ComputeRouter,
)
from harness.services.compute.types import (
    GLOBAL_PRICING_CATALOG,
    AssessmentTrace,
    ComplexityDimension,
    ComplexityVector,
    ComputeAssessedEvent,
    ComputeAssessment,
    ComputeEconomics,
    ComputeEconomicsEstimator,
    ModelPricingCatalog,
    ModelPricingRecord,
    ModelTier,
    ScoringProfile,
    ScoringProfileName,
    ThinkingBudget,
)

__all__ = [
    "COMPUTE_ASSESSOR_SERVICE",
    "AssessmentTrace",
    "BaseProviderAdapter",
    "ClaudeProviderAdapter",
    "ComplexityDimension",
    "ComplexityVector",
    "ComputeAssessedEvent",
    "ComputeAssessment",
    "ComputeAssessorPlugin",
    "ComputeAssessorService",
    "ComputeEconomics",
    "ComputeEconomicsEstimator",
    "ComputeRouter",
    "ComputeVisualBriefGenerator",
    "DeepSeekProviderAdapter",
    "DimensionalScorer",
    "DynamicTrajectoryEscalator",
    "FallbackLiteLLMAdapter",
    "GLOBAL_PRICING_CATALOG",
    "GeminiProviderAdapter",
    "ModelPricingCatalog",
    "ModelPricingRecord",
    "ModelTier",
    "OllamaProviderAdapter",
    "OpenAIProviderAdapter",
    "ProviderReasoningAdapter",
    "ProviderReasoningRegistry",
    "ScoringProfile",
    "ScoringProfileName",
    "ThinkingBudget",
    "TrajectoryState",
]
