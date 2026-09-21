"""Dynamic Model Router service protocol, typed models, and ServiceKey.

Elevates the 3-tier dynamic model switching & resilient failover engine
(Njoku 2026, ki_njoku_dynamic_model_routing) into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ComplexityProfileData(BaseModel):
    """Data transfer model for evaluated prompt complexity."""

    tier: str = Field(..., description="Resolved complexity tier (simple, medium, complex)")
    complexity_score: float = Field(..., description="Numerical complexity score from 0.0 to 1.0")
    token_count: int = Field(..., description="Estimated token count")
    word_count: int = Field(..., description="Word count")
    has_code_blocks: bool = Field(..., description="Whether prompt contains markdown code blocks")
    matched_keywords: list[str] = Field(default_factory=list, description="Matched reasoning keywords")
    duration_ms: float = Field(default=0.0, description="Evaluation latency in milliseconds")
    reasoning_depth_detected: bool = Field(default=False, description="Whether deep reasoning was triggered")
    tool_interaction_count: int = Field(default=0, description="Number of candidate tools evaluated")
    intent_tag: str = Field(default="", description="Semantic intent tag")


class ModelConfigData(BaseModel):
    """Data transfer model for model and provider parameters."""

    provider: str = Field(..., description="Cloud provider (e.g. openai, anthropic, gemini)")
    model_name: str = Field(..., description="Model identifier string")
    cost_per_1k_tokens: float = Field(default=0.0, description="Estimated cost per 1k tokens")
    reasoning_budget: str = Field(default="OFF", description="Thinking budget (OFF, LOW, HIGH)")
    timeout_seconds: float = Field(default=10.0, description="Socket timeout threshold in seconds")


class RoutingResolutionData(BaseModel):
    """Data transfer model for resolved model assignments."""

    complexity: str = Field(..., description="Assigned complexity tier")
    primary: ModelConfigData = Field(..., description="Designated primary model configuration")
    fallback: ModelConfigData = Field(..., description="Designated secondary fallback model configuration")
    fallback_chain: list[ModelConfigData] = Field(default_factory=list, description="Full candidate fallback chain")
    provider_diversity_enforced: bool = Field(default=True, description="Whether primary and fallback are on distinct providers")
    estimated_cost_per_1k: float = Field(default=0.0, description="Primary model cost per 1k tokens")
    reasoning_budget: str = Field(default="OFF", description="Assigned reasoning budget")


class NormalizedResponseData(BaseModel):
    """Data transfer model for canonical response envelope."""

    status: str = Field(..., description="Execution status (success, fallback_success, all_fallbacks_exhausted, circuit_breaker_open)")
    complexity_tier: str = Field(..., description="Evaluated complexity tier")
    primary_model: str = Field(..., description="Designated primary model")
    executed_model: str = Field(..., description="Model that successfully produced response")
    fallback_used: bool = Field(..., description="Whether secondary fallback was invoked")
    response: str = Field(..., description="Normalized text output")
    attempts: int = Field(default=1, description="Number of attempts taken")
    latency_ms: float = Field(default=0.0, description="Total execution latency in milliseconds")
    trace: list[str] = Field(default_factory=list, description="Execution step trace")
    error: str | None = Field(default=None, description="Error message if failed")


@runtime_checkable
class DynamicModelRouterService(Protocol):
    """Protocol for dynamic model routing, profiling, and resilient failover."""

    def profile_complexity(
        self, prompt: str, candidate_tools: Sequence[str] | None = None
    ) -> ComplexityProfileData:
        """Deterministic syntactic and token complexity evaluation in < 5ms."""
        ...

    def resolve_route(
        self, complexity: str, cost_ceiling: float | None = None
    ) -> RoutingResolutionData:
        """Resolve primary and fallback models asserting provider diversity."""
        ...

    def execute_request(
        self, prompt: str, override_complexity: str | None = None
    ) -> NormalizedResponseData:
        """Execute request through dynamic routing pipeline with fallback encasement."""
        ...

    def simulate_execution(
        self, prompt: str, failing_providers: list[str] | None = None
    ) -> NormalizedResponseData:
        """Simulate dynamic routing execution with injected provider failures."""
        ...

    def generate_visual_brief(
        self, output_path: str | Path | None = None
    ) -> Path:
        """Generate interactive HTML visual brief with telemetry and topology."""
        ...


DYNAMIC_MODEL_ROUTER_SERVICE_KEY: ServiceKey[DynamicModelRouterService] = ServiceKey(
    "service.dynamic_model_router"
)
