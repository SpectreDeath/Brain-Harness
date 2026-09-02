"""Tests validating the modular compute package and backward-compatible re-exports."""

import pytest

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
import harness.services.compute_assessor as legacy_assessor


def test_package_and_legacy_module_parity() -> None:
    """Verify that every public symbol in harness.services.compute is accessible in compute_assessor."""
    for symbol_name in [
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
    ]:
        pkg_symbol = globals().get(symbol_name)
        legacy_symbol = getattr(legacy_assessor, symbol_name, None)
        assert legacy_symbol is not None, f"Missing legacy export: {symbol_name}"
        assert pkg_symbol is legacy_symbol, f"Symbol identity mismatch for: {symbol_name}"


def test_compute_submodule_direct_imports() -> None:
    """Verify direct submodule imports from harness.services.compute.*."""
    from harness.services.compute.types import ThinkingBudget as TB, ModelTier as MT
    from harness.services.compute.scorer import DimensionalScorer as DS
    from harness.services.compute.providers import ProviderReasoningAdapter as PRA
    from harness.services.compute.brief import ComputeVisualBriefGenerator as CVBG
    from harness.services.compute.escalator import DynamicTrajectoryEscalator as DTE
    from harness.services.compute.service import ComputeAssessorService as CAS

    assert TB.HIGH.value == "high"
    assert MT.HIGH_REASONING.value == "high_reasoning"
    
    vector, trace = DS.evaluate(
        "Refactor kernel service registry and deepen architecture seams with multi-file topological sort",
        files_count=4,
        is_architecture=True,
    )
    assert vector.level == "High"
    
    payload = PRA.get_provider_payload("gemini-3.7-flash", TB.HIGH, 16384)
    assert payload["thinking_budget"] == "high"
    
    service = CAS()
    assessment = service.assess("Simple typo fix", files_count=1)
    assert assessment.complexity == "Low"
