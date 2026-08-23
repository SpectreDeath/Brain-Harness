"""Tests for deepened compute & model assessor subsystem."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, HarnessEvent, compute_event
from harness.kernel.context import ServiceContext
from harness.services.compute_assessor import (
    GLOBAL_PRICING_CATALOG,
    AssessmentTrace,
    BaseProviderAdapter,
    COMPUTE_ASSESSOR_SERVICE,
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
    DimensionalScorer,
    DynamicTrajectoryEscalator,
    ModelPricingCatalog,
    ModelPricingRecord,
    ModelTier,
    OllamaProviderAdapter,
    ProviderReasoningAdapter,
    ProviderReasoningRegistry,
    ScoringProfile,
    ScoringProfileName,
    ThinkingBudget,
    TrajectoryState,
)
from harness.services.llm import (
    ComputeAssessment as LLMComputeAssessment,
    ComputeRouter as LLMComputeRouter,
    LLMMessage,
    LLMResponse,
    LiteLLMService,
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
class TestScoringProfiles:
    """Test scoring profile presets and custom heuristics."""

    def test_scoring_profile_presets(self) -> None:
        heavy = ScoringProfile.get_preset(ScoringProfileName.REASONING_HEAVY)
        assert heavy.name == "reasoning_heavy"
        assert heavy.high_threshold < 0.65

        cost = ScoringProfile.get_preset(ScoringProfileName.COST_OPTIMIZED)
        assert cost.name == "cost_optimized"
        assert cost.high_threshold > 0.65

        latency = ScoringProfile.get_preset(ScoringProfileName.LATENCY_OPTIMIZED)
        assert latency.name == "latency_optimized"

    def test_custom_profile_with_keywords(self) -> None:
        custom_prof = ScoringProfile(
            name="security_heavy",
            custom_high_keywords={"zero_trust", "sanitization"},
            high_threshold=0.5,
        )
        vector, trace = DimensionalScorer.evaluate(
            "Review code for zero_trust architecture",
            profile=custom_prof,
        )
        assert "zero_trust" in trace.detected_keywords
        assert trace.profile_used == "security_heavy"


@pytest.mark.unit
class TestComputeEconomics:
    """Test token cost and latency estimation."""

    def test_pricing_and_latency_estimation(self) -> None:
        econ_gemini = ComputeEconomicsEstimator.estimate(
            "gemini-3.7-flash",
            ThinkingBudget.HIGH,
            16384,
        )
        assert econ_gemini.cost_per_million_input_usd > 0
        assert econ_gemini.expected_latency_p50_seconds > 0
        assert econ_gemini.estimated_query_cost_usd > 0
        assert "estimated_query_cost_usd" in econ_gemini.to_dict()

    def test_assessment_includes_economics(self) -> None:
        assessment = ComputeRouter.assess("Refactor database schema", files_count=3, is_architecture=True)
        assert assessment.economics is not None
        assert assessment.economics.cost_per_million_output_usd > 0
        dict_data = assessment.to_dict()
        assert "economics" in dict_data
        assert "Economics Projection" in assessment.format_recommendation_block()


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

    def test_ollama_payload_synthesis(self) -> None:
        payload = ProviderReasoningAdapter.get_provider_payload(
            "ollama/qwen2.5-coder:32b",
            ThinkingBudget.MEDIUM,
            4096,
        )
        assert "options" in payload
        assert payload["options"]["num_predict"] > 4096

    def test_custom_provider_adapter_registration(self) -> None:
        class CustomMockAdapter(BaseProviderAdapter):
            def can_handle(self, model_name: str) -> bool:
                return "mock-custom" in model_name

            def transform(
                self,
                model_name: str,
                thinking_level: ThinkingBudget,
                budget_tokens: int,
                *,
                temperature: float = 0.7,
                max_tokens: int | None = None,
            ) -> dict[str, Any]:
                return {
                    "model": model_name,
                    "custom_flag": True,
                    "budget": budget_tokens,
                }

        registry = ProviderReasoningRegistry()
        registry.register(CustomMockAdapter())
        res = registry.transform("mock-custom-v1", ThinkingBudget.HIGH, 10000)
        assert res["custom_flag"] is True
        assert res["budget"] == 10000


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
        assert "Token Economics" in content

        # Cleanup test artifact
        try:
            os.remove(html_path)
        except OSError:
            pass


@pytest.mark.unit
class TestComputeAssessorPluginAndIoC:
    """Test first-class HarnessPlugin lifecycle and IoC resolution."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_registration(self) -> None:
        ctx = ServiceContext()
        plugin = ComputeAssessorPlugin()
        
        await plugin.on_load(ctx)
        assert ctx.has(COMPUTE_ASSESSOR_SERVICE)
        
        service = ctx.require(COMPUTE_ASSESSOR_SERVICE)
        assert isinstance(service, ComputeAssessorService)
        
        assessment = service.assess("Refactor IoC container", is_architecture=True)
        assert assessment.complexity == "High"
        assert assessment.recommended_model == "gemini-3.7-flash"

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()


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
        assert "Economics Projection" in block

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
        assert "economics" in data

    def test_cli_assess_compute_html_brief(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["assess-compute", "Design new security sandbox", "--html"],
        )
        assert result.exit_code == 0
        assert "Generated Interactive HTML Visual Brief" in result.output


@pytest.mark.unit
class TestModelPricingCatalog:
    """Test dynamic model pricing catalog, overrides, and local fallback."""

    def test_default_catalog_pricing(self) -> None:
        catalog = ModelPricingCatalog()
        rec_gemini = catalog.get("gemini-3.7-flash")
        assert rec_gemini.input_per_m == 0.15
        assert rec_gemini.thinking_p50_s == 4.5

        rec_claude = catalog.get("claude-3-7-sonnet")
        assert rec_claude.input_per_m == 3.00
        assert rec_claude.output_per_m == 15.00

    def test_custom_pricing_registration(self) -> None:
        catalog = ModelPricingCatalog()
        catalog.register("my-finetuned-llama", ModelPricingRecord(input_per_m=0.05, output_per_m=0.10, p50_s=0.5))
        pricing = catalog.get("my-finetuned-llama")
        assert pricing.input_per_m == 0.05
        assert pricing.p50_s == 0.5

    def test_ollama_local_zero_cost_fallback(self) -> None:
        catalog = ModelPricingCatalog()
        pricing = catalog.get("ollama/qwen2.5-coder:32b")
        assert pricing.input_per_m == 0.0
        assert pricing.output_per_m == 0.0

    def test_global_catalog_singleton(self) -> None:
        GLOBAL_PRICING_CATALOG.register("custom-model-x", {"input_per_m": 0.20, "output_per_m": 0.80})
        econ = ComputeEconomicsEstimator.estimate("custom-model-x", ThinkingBudget.HIGH, 4096)
        assert econ.cost_per_million_input_usd == 0.20
        assert econ.cost_per_million_output_usd == 0.80


@pytest.mark.unit
class TestMultiTurnConversationAssessment:
    """Test assess_conversation evaluating LLMMessages and trajectory tool calls."""

    def test_assess_conversation_with_tool_calls_and_debugging(self) -> None:
        messages = [
            LLMMessage(role="system", content="You are a senior systems engineer."),
            LLMMessage(role="user", content="We have a deadlock race condition in kernel context.py!"),
            LLMMessage(role="assistant", content="Let me investigate.", tool_call_id="call_1"),
            LLMMessage(role="tool", content="Traceback (most recent call last): DeadlockError in line 42"),
            LLMMessage(role="assistant", content="Found the locking bug. Refactoring mutex.", tool_call_id="call_2"),
            LLMMessage(role="tool", content="Mutex released successfully."),
        ]
        assessment = ComputeRouter.assess_conversation(messages)
        assert assessment.complexity == "High"
        assert assessment.recommended_model == "gemini-3.7-flash"
        assert assessment.budget_tokens == 16384
        assert assessment.vector is not None
        assert assessment.vector.concurrency_score >= 0.4
        assert any("tool calls" in f.lower() for f in assessment.trace.high_factors)

    def test_assess_conversation_low_mechanical(self) -> None:
        messages = [
            LLMMessage(role="user", content="Please format docstrings and sort imports in helper.py"),
            LLMMessage(role="assistant", content="Done."),
        ]
        assessment = ComputeRouter.assess_conversation(messages)
        assert assessment.complexity == "Low"
        assert assessment.recommended_model == "gemini-2.0-flash"
        assert assessment.budget_tokens == 0

    def test_service_assess_conversation_method(self) -> None:
        service = ComputeAssessorService()
        messages = [
            {"role": "user", "content": "Refactor architecture seams across kernel context.py and registry.py"},
        ]
        assessment = service.assess_conversation(messages)
        assert assessment.complexity == "High"


@pytest.mark.unit
class TestLiteLLMReasoningDeepSeam:
    """Test LiteLLMService integration with ProviderReasoningAdapter."""

    @pytest.mark.asyncio
    async def test_litellm_complete_passes_provider_params(self) -> None:
        service = LiteLLMService()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello", tool_calls=[]), finish_reason="stop")]
        mock_response.model = "gemini-3.7-flash"
        mock_response.usage = {"total_tokens": 100}
        mock_response.model_dump.return_value = {}

        mock_litellm = MagicMock()
        mock_acomplete = AsyncMock(return_value=mock_response)
        mock_litellm.acompletion = mock_acomplete

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            res = await service.complete(
                [LLMMessage(role="user", content="Test prompt")],
                model="gemini-3.7-flash",
                thinking_budget=ThinkingBudget.HIGH,
                budget_tokens=16384,
            )

            assert res.content == "Hello"
            mock_acomplete.assert_called_once()
            call_kwargs = mock_acomplete.call_args[1]
            assert "thinking_config" in call_kwargs
            assert call_kwargs["thinking_config"]["thinking_budget"] == 16384
            assert call_kwargs["thinking_budget"] == "high"

    @pytest.mark.asyncio
    async def test_litellm_claude_budget_tokens(self) -> None:
        service = LiteLLMService()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello", tool_calls=[]), finish_reason="stop")]
        mock_response.model = "claude-3-7-sonnet"
        mock_response.usage = {"total_tokens": 100}
        mock_response.model_dump.return_value = {}

        mock_litellm = MagicMock()
        mock_acomplete = AsyncMock(return_value=mock_response)
        mock_litellm.acompletion = mock_acomplete

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            await service.complete(
                [LLMMessage(role="user", content="Refactor architecture")],
                model="claude-3-7-sonnet",
                thinking_budget=ThinkingBudget.HIGH,
                budget_tokens=16000,
            )

            call_kwargs = mock_acomplete.call_args[1]
            assert "thinking" in call_kwargs
            assert call_kwargs["thinking"]["budget_tokens"] == 16000


@pytest.mark.unit
class TestComputeTelemetryEvents:
    """Test ComputeAssessedEvent model and EventBus telemetry."""

    @pytest.mark.asyncio
    async def test_compute_assessed_event_emission(self) -> None:
        bus = EventBus()
        captured_events: list[HarnessEvent] = []

        bus.on(EventType.COMPUTE_ASSESSED, lambda e: captured_events.append(e))

        assessment = ComputeRouter.assess("Refactor kernel core", is_architecture=True)
        event = compute_event(
            EventType.COMPUTE_ASSESSED,
            complexity=assessment.complexity,
            model_tier=assessment.model_tier.value,
            recommended_model=assessment.recommended_model,
            budget_tokens=assessment.budget_tokens,
            composite_score=assessment.vector.composite_score if assessment.vector else 0.0,
            estimated_cost_usd=assessment.economics.estimated_query_cost_usd if assessment.economics else 0.0,
        )
        await bus.emit(event)

        assert len(captured_events) == 1
        assert captured_events[0].event_type == EventType.COMPUTE_ASSESSED
        assert captured_events[0].payload["complexity"] == "High"
        assert captured_events[0].payload["recommended_model"] == "gemini-3.7-flash"

    def test_compute_assessed_event_pydantic_schema(self) -> None:
        event = ComputeAssessedEvent(
            complexity="High",
            model_tier="high_reasoning",
            recommended_model="gemini-3.7-flash",
            budget_tokens=16384,
            composite_score=0.88,
            estimated_cost_usd=0.0105,
        )
        data = event.model_dump()
        assert data["complexity"] == "High"
        assert data["budget_tokens"] == 16384
        assert data["composite_score"] == 0.88


@pytest.mark.unit
class TestComputeAssessorServiceEventBusIntegration:
    """Test ComputeAssessorService IoC locality, event bus wiring, and audit log."""

    @pytest.mark.asyncio
    async def test_service_with_event_bus_and_audit_log(self) -> None:
        bus = EventBus()
        captured_events: list[HarnessEvent] = []
        bus.on(EventType.COMPUTE_ASSESSED, lambda e: captured_events.append(e))

        custom_catalog = ModelPricingCatalog()
        custom_registry = ProviderReasoningRegistry()
        service = ComputeAssessorService(
            default_profile=ScoringProfileName.BALANCED,
            catalog=custom_catalog,
            registry=custom_registry,
            event_bus=bus,
        )

        assert service.catalog is custom_catalog
        assert service.registry is custom_registry
        assert service.event_bus is bus

        assessment = await service.assess_and_publish("Refactor kernel core", is_architecture=True)
        assert assessment.complexity == "High"
        assert len(service.audit_log) == 1
        assert service.audit_log[0].complexity == "High"
        assert len(captured_events) == 1
        assert captured_events[0].payload["complexity"] == "High"

    @pytest.mark.asyncio
    async def test_plugin_wires_event_bus_from_context(self) -> None:
        ctx = ServiceContext()
        bus = EventBus()
        ctx.provide(EVENT_BUS_KEY, bus)

        plugin = ComputeAssessorPlugin()
        await plugin.on_load(ctx)

        resolved_service = ctx.require(COMPUTE_ASSESSOR_SERVICE)
        assert resolved_service.event_bus is bus


@pytest.mark.unit
class TestDynamicTrajectoryEscalator:
    """Test DynamicTrajectoryEscalator budget ramping, failure escalation, and tree allocation."""

    def test_no_escalation_on_clean_first_attempt(self) -> None:
        base = ComputeRouter.assess("Format docstrings")
        traj = TrajectoryState()
        escalated = DynamicTrajectoryEscalator.escalate(base, traj)
        assert escalated.complexity == base.complexity
        assert escalated.budget_tokens == base.budget_tokens
        assert not traj.is_escalated

    def test_escalate_from_fast_mechanical_on_error(self) -> None:
        base = ComputeRouter.assess("Format docstrings")
        assert base.model_tier == ModelTier.FAST_MECHANICAL
        assert base.budget_tokens == 0

        traj = TrajectoryState()
        traj.record_attempt(success=False, error="SyntaxError: invalid syntax")

        escalated = DynamicTrajectoryEscalator.escalate(base, traj)
        assert escalated.model_tier == ModelTier.STANDARD_AGENTIC
        assert escalated.thinking_level == ThinkingBudget.MEDIUM
        assert escalated.budget_tokens == 4096
        assert traj.is_escalated
        assert traj.current_tier == ModelTier.STANDARD_AGENTIC

    def test_escalate_from_standard_agentic_on_error(self) -> None:
        base = ComputeRouter.assess("Add helper function to string utils")
        assert base.model_tier == ModelTier.STANDARD_AGENTIC
        assert base.budget_tokens == 4096

        traj = TrajectoryState()
        traj.record_attempt(success=False, error="AssertionError in unit test")

        escalated = DynamicTrajectoryEscalator.escalate(base, traj)
        assert escalated.model_tier == ModelTier.HIGH_REASONING
        assert escalated.thinking_level == ThinkingBudget.HIGH
        assert escalated.budget_tokens == 16384
        assert traj.is_escalated

    def test_escalate_to_max_reasoning_on_consecutive_failures(self) -> None:
        base = ComputeRouter.assess("Refactor architecture seams", is_architecture=True)
        assert base.model_tier == ModelTier.HIGH_REASONING

        traj = TrajectoryState()
        traj.record_attempt(success=False, error="Deadlock detected")
        traj.record_attempt(success=False, error="Second timeout in cycle")

        escalated = DynamicTrajectoryEscalator.escalate(base, traj)
        assert escalated.model_tier == ModelTier.HIGH_REASONING
        assert escalated.budget_tokens >= 24576
        assert "MAX reasoning budget" in escalated.reasoning

    def test_tree_budget_allocation(self) -> None:
        allocated = DynamicTrajectoryEscalator.allocate_tree_budget(
            total_budget_tokens=32000,
            branch_weights=[0.5, 0.25, 0.25],
        )
        assert len(allocated) == 3
        assert sum(allocated) == 32000
        assert allocated[0] == 16000
        assert allocated[1] == 8000
        assert allocated[2] == 8000

    def test_tree_budget_allocation_empty_or_zero_weights(self) -> None:
        assert DynamicTrajectoryEscalator.allocate_tree_budget(10000, []) == []
        equal = DynamicTrajectoryEscalator.allocate_tree_budget(10000, [0.0, 0.0])
        assert equal == [5000, 5000]

    def test_service_escalate_method(self) -> None:
        service = ComputeAssessorService()
        base = service.assess("Format code")
        traj = TrajectoryState()
        traj.record_attempt(success=False, error="FormatError")
        escalated = service.escalate(base, traj)
        assert escalated.model_tier == ModelTier.STANDARD_AGENTIC
        assert len(service.audit_log) == 2


@pytest.mark.unit
class TestInteractiveVisualBriefStudio:
    """Test interactive visual brief generation containing multi-provider payload studio."""

    def test_visual_brief_contains_interactive_studio_and_payloads(self) -> None:
        assessment = ComputeRouter.assess("Refactor kernel core", is_architecture=True)
        html_path = ComputeVisualBriefGenerator.render_to_temp(assessment, task_title="Test Studio Brief")

        assert os.path.exists(html_path)
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Live Provider Payload Studio" in content
        assert "gemini-3.7-flash" in content
        assert "claude-3-7-sonnet" in content
        assert "o3-mini" in content
        assert "deepseek-r1" in content
        assert "ollama/qwen2.5-coder:32b" in content
        assert "selectTab('gemini')" in content
        assert "copyPayload()" in content
        assert "Mermaid" in content or "mermaid.initialize" in content

