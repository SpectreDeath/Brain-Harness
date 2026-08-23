"""Tests for deepened compute & model assessor subsystem."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.services.compute_assessor import (
    AssessmentTrace,
    ComplexityDimension,
    ComplexityVector,
    ComputeAssessment,
    ComputeRouter,
    ComputeVisualBriefGenerator,
    DimensionalScorer,
    ModelTier,
    ProviderReasoningAdapter,
    ThinkingBudget,
)
from harness.services.llm import (
    ComputeAssessment as LLMComputeAssessment,
    ComputeRouter as LLMComputeRouter,
    ModelTier as LLMModelTier,
    ThinkingBudget as LLMThinkingBudget,
)


@pytest.mark.unit
class TestDimensionalScorer:
    """Test 5-dimensional vector evaluation, keyword weights, and trace generation."""

    def test_high_complexity_architectural_vector(self) -> None:
        vector, trace = DimensionalScorer.evaluate(
            "Refactor kernel service registry and deepen architecture seams with multi-file topological sort",
            files_count=4,
            is_architecture=True,
        )
        assert vector.level == "High"
        assert vector.composite_score >= 0.6
        assert vector.span_score >= 0.8
        assert vector.depth_score >= 0.5
        assert trace.is_architectural is True
        assert len(trace.high_factors) > 0
        assert any("topological" in kw or "refactor" in kw for kw in trace.detected_keywords)

    def test_low_complexity_mechanical_vector(self) -> None:
        vector, trace = DimensionalScorer.evaluate(
            "Format docstrings and fix regex syntax in helper script",
            files_count=1,
            is_architecture=False,
            is_debugging=False,
        )
        assert vector.level == "Low"
        assert vector.composite_score < 0.35
        assert len(trace.low_factors) > 0
        assert trace.files_evaluated == 1

    def test_concurrency_and_debugging_dimensions(self) -> None:
        vector, trace = DimensionalScorer.evaluate(
            "Debug asyncio deadlock and race condition in event loop mutex",
            files_count=2,
            is_debugging=True,
        )
        assert vector.concurrency_score >= 0.6
        assert vector.ambiguity_score >= 0.6
        assert vector.level == "High"
        assert trace.is_debugging is True

    def test_vector_and_trace_serialization(self) -> None:
        vector, trace = DimensionalScorer.evaluate("Refactor database migration schema", files_count=3)
        v_dict = vector.to_dict()
        t_dict = trace.to_dict()

        assert "composite" in v_dict
        assert "ambiguity" in v_dict
        assert "high_factors" in t_dict
        assert isinstance(t_dict["detected_keywords"], list)


@pytest.mark.unit
class TestProviderReasoningAdapter:
    """Test vendor-specific parameter and payload synthesis."""

    def test_gemini_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "gemini-3.7-flash",
            ThinkingBudget.HIGH,
            16384,
            temperature=0.5,
        )
        assert payload["model"] == "gemini-3.7-flash"
        assert payload["temperature"] == 0.5
        assert "thinking_config" in payload
        assert payload["thinking_config"]["thinking_budget"] == 16384
        assert payload["thinking_budget"] == "high"

    def test_gemini_off_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "gemini-2.0-flash",
            ThinkingBudget.OFF,
            0,
        )
        assert payload["thinking_config"]["thinking_budget"] == 0
        assert payload["thinking_budget"] == "off"

    def test_claude_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "claude-3-7-sonnet",
            ThinkingBudget.HIGH,
            16000,
        )
        assert payload["thinking"]["type"] == "enabled"
        assert payload["thinking"]["budget_tokens"] == 16000
        assert payload["max_tokens"] > 16000

    def test_openai_o_series_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "o3-mini",
            ThinkingBudget.HIGH,
            16384,
        )
        assert payload["reasoning_effort"] == "high"

    def test_deepseek_r1_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "deepseek-r1",
            ThinkingBudget.HIGH,
            16384,
        )
        assert "extra_body" in payload
        assert payload["extra_body"]["reasoning_effort"] == "high"


@pytest.mark.unit
class TestComputeVisualBriefGenerator:
    """Test interactive dark-mode HTML generation in %TEMP%."""

    def test_html_visual_brief_generation(self) -> None:
        assessment = ComputeRouter.assess(
            "Refactor kernel service registry and topological sort",
            files_count=4,
            is_architecture=True,
        )
        html_path = ComputeVisualBriefGenerator.render_to_temp(assessment, task_title="Test Visual Brief")
        
        assert os.path.exists(html_path)
        assert html_path.endswith(".html")

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "<!DOCTYPE html>" in content
        assert "mermaid" in content
        assert "5-Dimensional Complexity Vector" in content
        assert "gemini-3.7-flash" in content
        assert "TIER: HIGH" in content

        # Cleanup test artifact
        try:
            os.remove(html_path)
        except OSError:
            pass


@pytest.mark.unit
class TestComputeRouterDeepened:
    """Test facade integration and backward compatibility with llm.py."""

    def test_llm_service_reexport_parity(self) -> None:
        assert LLMModelTier is ModelTier
        assert LLMThinkingBudget is ThinkingBudget
        assert LLMComputeAssessment is ComputeAssessment
        assert LLMComputeRouter is ComputeRouter

    def test_detailed_assessment_formatting(self) -> None:
        assessment = ComputeRouter.assess("Migrate persistent storage schema", is_architecture=True)
        block = assessment.format_recommendation_block()
        assert "### [Compute Recommendation Block]" in block
        assert "Complexity Assessment" in block
        assert "Vector Breakdown" in block

    def test_synthesize_payload_convenience_method(self) -> None:
        assessment = ComputeRouter.assess("Refactor kernel core", is_architecture=True)
        payload = ComputeRouter.synthesize_payload(assessment)
        assert payload["model"] == "gemini-3.7-flash"
        assert payload["thinking_budget"] == "high"


@pytest.mark.unit
class TestComputeAssessorCLI:
    """Test harness assess-compute CLI command."""

    def test_cli_assess_compute_markdown_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["assess-compute", "Refactor service registry", "--arch", "--files", "4"],
        )
        assert result.exit_code == 0
        assert "### [Compute Recommendation Block]" in result.output
        assert "gemini-3.7-flash" in result.output

    def test_cli_assess_compute_json_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["assess-compute", "Format docstrings", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "complexity" in data
        assert "model_tier" in data
        assert "vector" in data

    def test_cli_assess_compute_html_brief(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["assess-compute", "Design new security sandbox", "--html"],
        )
        assert result.exit_code == 0
        assert "Generated Interactive HTML Visual Brief" in result.output
