"""Unit tests for compute model assessor and dynamic reasoning budget router."""

from __future__ import annotations

import pytest

from harness.services.llm import (
    ComputeAssessment,
    ComputeRouter,
    ModelTier,
    ThinkingBudget,
)


@pytest.mark.unit
class TestComputeModelAssessor:
    """Test ComputeRouter classification, reasoning budget calibration, and override logic."""

    def test_high_complexity_architectural_classification(self) -> None:
        assessment = ComputeRouter.assess(
            "Refactor kernel service registry and deepen architecture seams with multi-file topological sort",
            files_count=4,
            is_architecture=True,
        )
        assert assessment.complexity == "High"
        assert assessment.model_tier == ModelTier.HIGH_REASONING
        assert assessment.thinking_level == ThinkingBudget.HIGH
        assert assessment.budget_tokens >= 16000
        assert "gemini-3.7-flash" in assessment.recommended_model
        assert "claude-3-7-sonnet" in assessment.alternative_models
        assert "o3-mini" in assessment.alternative_models

    def test_low_complexity_mechanical_classification(self) -> None:
        assessment = ComputeRouter.assess(
            "Format docstrings and fix regex syntax in helper script",
            files_count=1,
            is_architecture=False,
            is_debugging=False,
        )
        assert assessment.complexity == "Low"
        assert assessment.model_tier == ModelTier.FAST_MECHANICAL
        assert assessment.thinking_level == ThinkingBudget.OFF
        assert assessment.budget_tokens == 0
        assert "gemini-2.0-flash" in assessment.recommended_model
        assert "gpt-4o-mini" in assessment.alternative_models

    def test_medium_complexity_standard_agentic_classification(self) -> None:
        assessment = ComputeRouter.assess(
            "Implement a new unit test class for storage repository",
            files_count=1,
            is_architecture=False,
            is_debugging=False,
        )
        assert assessment.complexity == "Medium"
        assert assessment.model_tier == ModelTier.STANDARD_AGENTIC
        assert assessment.thinking_level == ThinkingBudget.MEDIUM
        assert assessment.budget_tokens == 4096
        assert "gemini-3.7-flash" in assessment.recommended_model

    def test_manual_override_tiers(self) -> None:
        # Override to High Reasoning
        assessment_high = ComputeRouter.assess(
            "simple typo fix",
            override_tier=ModelTier.HIGH_REASONING,
        )
        assert assessment_high.complexity == "High"
        assert assessment_high.thinking_level == ThinkingBudget.HIGH

        # Override to Fast Mechanical
        assessment_low = ComputeRouter.assess(
            "complex architectural DAG migration",
            override_tier=ModelTier.FAST_MECHANICAL,
        )
        assert assessment_low.complexity == "Low"
        assert assessment_low.thinking_level == ThinkingBudget.OFF

    def test_assessment_to_dict_serialization(self) -> None:
        assessment = ComputeRouter.assess("Refactor database schema", files_count=2, is_architecture=True)
        data = assessment.to_dict()
        assert isinstance(data, dict)
        assert data["complexity"] == "High"
        assert data["model_tier"] == "high_reasoning"
        assert data["thinking_level"] == "high"
        assert data["budget_tokens"] == 16384
        assert isinstance(data["alternative_models"], list)
