"""Compute & Model Assessor Subsystem — Backward-compatible facade module.

.. deprecated:: 2.0.0
   This facade module is deprecated. The canonical import path for all compute
   and model assessment symbols is ``harness.services.compute``.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "harness.services.compute_assessor is deprecated; import directly from harness.services.compute instead.",
    DeprecationWarning,
    stacklevel=2,
)

from harness.services.compute import (
    COMPUTE_ASSESSOR_SERVICE,
    AssessmentTrace,
    BaseProviderAdapter,
    ClaudeProviderAdapter,
    ComplexityDimension,
    ComplexityVector,
    ComputeAssessedEvent,
    ComputeAssessment,
    ComputeAssessorPlugin,
    ComputeAssessorService,
    ComputeEconomics,
    ComputeEconomicsEstimator,
    ComputeRouter,
    ComputeVisualBriefGenerator,
    DeepSeekProviderAdapter,
    DimensionalScorer,
    DynamicTrajectoryEscalator,
    FallbackLiteLLMAdapter,
    GLOBAL_PRICING_CATALOG,
    GeminiProviderAdapter,
    ModelPricingCatalog,
    ModelPricingRecord,
    ModelTier,
    OllamaProviderAdapter,
    OpenAIProviderAdapter,
    ProviderReasoningAdapter,
    ProviderReasoningRegistry,
    ScoringProfile,
    ScoringProfileName,
    ThinkingBudget,
    TrajectoryState,
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
