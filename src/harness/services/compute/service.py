"""Compute router, stateful service, IoC registration, and plugin definition."""

from __future__ import annotations

from typing import Any

import structlog

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, compute_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.compute.brief import ComputeVisualBriefGenerator
from harness.services.compute.escalator import (
    DynamicTrajectoryEscalator,
    TrajectoryState,
)
from harness.services.compute.providers import (
    _GLOBAL_PROVIDER_REGISTRY,
    ProviderReasoningAdapter,
    ProviderReasoningRegistry,
)
from harness.services.compute.scorer import DimensionalScorer
from harness.services.compute.types import (
    GLOBAL_PRICING_CATALOG,
    AssessmentTrace,
    ComplexityVector,
    ComputeAssessedEvent,
    ComputeAssessment,
    ComputeEconomicsEstimator,
    ModelPricingCatalog,
    ModelTier,
    ScoringProfile,
    ScoringProfileName,
    ThinkingBudget,
)

logger = structlog.get_logger()


class ComputeRouter:
    """Evaluates task surface complexity and recommends optimal compute budget."""

    @classmethod
    def assess(
        cls,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        override_tier: ModelTier | None = None,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> ComputeAssessment:
        """Classify task complexity and return a calibrated compute recommendation."""
        # 1. Check manual overrides
        if override_tier == ModelTier.HIGH_REASONING:
            vector = ComplexityVector(composite_score=0.9, level="High")
            trace = AssessmentTrace(notes="Manual override set to High Reasoning tier.")
            econ = ComputeEconomicsEstimator.estimate("gemini-3.7-flash", ThinkingBudget.HIGH, 16384)
            return ComputeAssessment(
                complexity="High",
                model_tier=ModelTier.HIGH_REASONING,
                thinking_level=ThinkingBudget.HIGH,
                recommended_model="gemini-3.7-flash",
                budget_tokens=16384,
                alternative_models=["claude-3-7-sonnet", "o3-mini", "deepseek-r1"],
                reasoning="Manual override set to High Reasoning tier.",
                vector=vector,
                trace=trace,
                economics=econ,
            )
        elif override_tier == ModelTier.FAST_MECHANICAL:
            vector = ComplexityVector(composite_score=0.1, level="Low")
            trace = AssessmentTrace(notes="Manual override set to Fast Mechanical tier.")
            econ = ComputeEconomicsEstimator.estimate("gemini-2.0-flash", ThinkingBudget.OFF, 0)
            return ComputeAssessment(
                complexity="Low",
                model_tier=ModelTier.FAST_MECHANICAL,
                thinking_level=ThinkingBudget.OFF,
                recommended_model="gemini-2.0-flash",
                budget_tokens=0,
                alternative_models=["gpt-4o-mini", "claude-3-5-haiku"],
                reasoning="Manual override set to Fast Mechanical tier.",
                vector=vector,
                trace=trace,
                economics=econ,
            )
        elif override_tier == ModelTier.STANDARD_AGENTIC:
            vector = ComplexityVector(composite_score=0.5, level="Medium")
            trace = AssessmentTrace(notes="Manual override set to Standard Agentic tier.")
            econ = ComputeEconomicsEstimator.estimate("gemini-3.7-flash", ThinkingBudget.MEDIUM, 4096)
            return ComputeAssessment(
                complexity="Medium",
                model_tier=ModelTier.STANDARD_AGENTIC,
                thinking_level=ThinkingBudget.MEDIUM,
                recommended_model="gemini-3.7-flash",
                budget_tokens=4096,
                alternative_models=["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"],
                reasoning="Manual override set to Standard Agentic tier.",
                vector=vector,
                trace=trace,
                economics=econ,
            )

        # 2. Dimensional scoring with profile
        vector, trace = DimensionalScorer.evaluate(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile,
        )

        if vector.level == "High":
            rec_model = "gemini-3.7-flash"
            budget = 16384
            thinking = ThinkingBudget.HIGH
            tier = ModelTier.HIGH_REASONING
            alts = ["claude-3-7-sonnet", "o3-mini", "deepseek-r1"]
            reason = "High complexity: cross-module scope, structural ambiguity, or architectural constraints."
        elif vector.level == "Low":
            rec_model = "gemini-2.0-flash"
            budget = 0
            thinking = ThinkingBudget.OFF
            tier = ModelTier.FAST_MECHANICAL
            alts = ["gpt-4o-mini", "claude-3-5-haiku", "mistral-small"]
            reason = "Low complexity: mechanical syntax, parsing, or linear boilerplate."
        else:
            rec_model = "gemini-3.7-flash"
            budget = 4096
            thinking = ThinkingBudget.MEDIUM
            tier = ModelTier.STANDARD_AGENTIC
            alts = ["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"]
            reason = "Medium complexity: standard single-module feature implementation or unit test creation."

        econ = ComputeEconomicsEstimator.estimate(rec_model, thinking, budget)

        return ComputeAssessment(
            complexity=vector.level,
            model_tier=tier,
            thinking_level=thinking,
            recommended_model=rec_model,
            budget_tokens=budget,
            alternative_models=alts,
            reasoning=reason,
            vector=vector,
            trace=trace,
            economics=econ,
        )

    @classmethod
    def assess_conversation(
        cls,
        messages: list[Any],
        *,
        override_tier: ModelTier | None = None,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> ComputeAssessment:
        """Assess multi-turn conversation messages and return a calibrated compute recommendation."""
        vector, trace = DimensionalScorer.evaluate_conversation(messages, profile=profile)

        if override_tier:
            return cls.assess("", override_tier=override_tier, profile=profile)

        if vector.level == "High":
            rec_model = "gemini-3.7-flash"
            budget = 16384
            thinking = ThinkingBudget.HIGH
            tier = ModelTier.HIGH_REASONING
            alts = ["claude-3-7-sonnet", "o3-mini", "deepseek-r1"]
            reason = "High complexity: cross-module scope, structural ambiguity, or architectural constraints."
        elif vector.level == "Low":
            rec_model = "gemini-2.0-flash"
            budget = 0
            thinking = ThinkingBudget.OFF
            tier = ModelTier.FAST_MECHANICAL
            alts = ["gpt-4o-mini", "claude-3-5-haiku", "mistral-small"]
            reason = "Low complexity: mechanical syntax, parsing, or linear boilerplate."
        else:
            rec_model = "gemini-3.7-flash"
            budget = 4096
            thinking = ThinkingBudget.MEDIUM
            tier = ModelTier.STANDARD_AGENTIC
            alts = ["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"]
            reason = "Medium complexity: standard single-module feature implementation or unit test creation."

        econ = ComputeEconomicsEstimator.estimate(rec_model, thinking, budget)

        return ComputeAssessment(
            complexity=vector.level,
            model_tier=tier,
            thinking_level=thinking,
            recommended_model=rec_model,
            budget_tokens=budget,
            alternative_models=alts,
            reasoning=reason,
            vector=vector,
            trace=trace,
            economics=econ,
        )

    @classmethod
    def generate_visual_brief(
        cls,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
        task_title: str = "Compute Assessment",
    ) -> str:
        """Assess prompt and generate an interactive HTML visual brief in %TEMP%."""
        assessment = cls.assess(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile,
        )
        return ComputeVisualBriefGenerator.render_to_temp(assessment, task_title=task_title)

    @classmethod
    def synthesize_payload(
        cls,
        assessment: ComputeAssessment,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize provider-specific payload for the assessed model configuration."""
        target_model = model or assessment.recommended_model
        return ProviderReasoningAdapter.get_provider_payload(
            target_model,
            assessment.thinking_level,
            assessment.budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )


class ComputeAssessorService:
    """Stateful compute assessor service for IoC container resolution with EventBus telemetry."""

    def __init__(
        self,
        default_profile: ScoringProfileName | str = ScoringProfileName.BALANCED,
        catalog: ModelPricingCatalog | None = None,
        registry: ProviderReasoningRegistry | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.default_profile = default_profile
        self._catalog = catalog or GLOBAL_PRICING_CATALOG
        self._registry = registry or _GLOBAL_PROVIDER_REGISTRY
        self._event_bus = event_bus
        self._audit_log: list[ComputeAssessedEvent] = []

    @property
    def catalog(self) -> ModelPricingCatalog:
        return self._catalog

    @property
    def registry(self) -> ProviderReasoningRegistry:
        return self._registry

    @property
    def event_bus(self) -> EventBus | None:
        return self._event_bus

    @property
    def audit_log(self) -> list[ComputeAssessedEvent]:
        return list(self._audit_log)

    def set_event_bus(self, event_bus: EventBus | None) -> None:
        """Attach or update the authoritative event bus for telemetry publication."""
        self._event_bus = event_bus

    def assess(
        self,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        override_tier: ModelTier | None = None,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> ComputeAssessment:
        assessment = ComputeRouter.assess(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            override_tier=override_tier,
            profile=profile or self.default_profile,
        )
        self._record_telemetry(assessment)
        return assessment

    def assess_conversation(
        self,
        messages: list[Any],
        *,
        override_tier: ModelTier | None = None,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> ComputeAssessment:
        assessment = ComputeRouter.assess_conversation(
            messages,
            override_tier=override_tier,
            profile=profile or self.default_profile,
        )
        self._record_telemetry(assessment)
        return assessment

    def escalate(
        self,
        base_assessment: ComputeAssessment,
        trajectory: TrajectoryState,
    ) -> ComputeAssessment:
        """Escalate compute budget based on multi-attempt trajectory state."""
        escalated = DynamicTrajectoryEscalator.escalate(base_assessment, trajectory, catalog=self._catalog)
        self._record_telemetry(escalated)
        return escalated

    async def assess_and_publish(
        self,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        override_tier: ModelTier | None = None,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> ComputeAssessment:
        """Assess task and asynchronously publish compute event to the event bus."""
        assessment = self.assess(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            override_tier=override_tier,
            profile=profile,
        )
        await self._publish_to_bus(assessment)
        return assessment

    def synthesize_payload(
        self,
        assessment: ComputeAssessment,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        target_model = model or assessment.recommended_model
        return self._registry.transform(
            target_model,
            assessment.thinking_level,
            assessment.budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_visual_brief(
        self,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
        task_title: str = "Compute Assessment",
    ) -> str:
        return ComputeRouter.generate_visual_brief(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile or self.default_profile,
            task_title=task_title,
        )

    def _record_telemetry(self, assessment: ComputeAssessment) -> None:
        """Create audit event and record to the internal audit log."""
        event_data = ComputeAssessedEvent(
            complexity=assessment.complexity,
            model_tier=assessment.model_tier.value,
            recommended_model=assessment.recommended_model,
            budget_tokens=assessment.budget_tokens,
            composite_score=assessment.vector.composite_score if assessment.vector else 0.5,
            estimated_cost_usd=assessment.economics.estimated_query_cost_usd if assessment.economics else 0.0,
        )
        self._audit_log.append(event_data)

    async def _publish_to_bus(self, assessment: ComputeAssessment) -> None:
        if not self._event_bus:
            return
        event = compute_event(
            event_type=EventType.COMPUTE_ASSESSED,
            source="compute.assessor",
            complexity=assessment.complexity,
            model_tier=assessment.model_tier.value,
            recommended_model=assessment.recommended_model,
            budget_tokens=assessment.budget_tokens,
            composite_score=assessment.vector.composite_score if assessment.vector else 0.5,
            estimated_cost_usd=assessment.economics.estimated_query_cost_usd if assessment.economics else 0.0,
        )
        await self._event_bus.emit(event)


# Typed service key for IoC container
COMPUTE_ASSESSOR_SERVICE = ServiceKey[ComputeAssessorService]("compute.assessor")


class ComputeAssessorPlugin(HarnessPlugin):
    """Harness plugin providing the ComputeAssessorService to the IoC container."""

    name = "compute.assessor"
    version = "2.2.0"
    description = "Compute and Model Assessor routing, scoring, and reasoning budget service"
    provides = [COMPUTE_ASSESSOR_SERVICE]
    trusted = True

    def __init__(self, default_profile: ScoringProfileName | str = ScoringProfileName.BALANCED) -> None:
        self._service = ComputeAssessorService(default_profile=default_profile)

    async def on_load(self, ctx: ServiceContext) -> None:
        if ctx.has(EVENT_BUS_KEY):
            bus = ctx.require(EVENT_BUS_KEY)
            self._service.set_event_bus(bus)
        ctx.provide(COMPUTE_ASSESSOR_SERVICE, self._service)
        logger.info("compute_assessor_plugin_loaded", version=self.version)

    async def on_enable(self) -> None:
        logger.info("compute_assessor_plugin_enabled")

    async def on_disable(self) -> None:
        logger.info("compute_assessor_plugin_disabled")

    async def on_unload(self) -> None:
        logger.info("compute_assessor_plugin_unloaded")
