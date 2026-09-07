"""3-Tier Dynamic Model Switching & Resilient Fallback Engine.

Distilled from 'How to Build AI Applications That Switch Models Automatically' by Chidiebere Njoku.
Implements:
- Tier 1: Deterministic prompt complexity and intent analysis.
- Tier 2: Cost-calibrated model tier selection (Flash vs Frontier Reasoning).
- Tier 3: Resilient automated fallback chaining with circuit breaker protection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any


@dataclass(slots=True, frozen=True)
class ComplexityScore:
    """Tier 1: Evaluated prompt complexity and intent classification."""

    tier: str  # "LOW", "MEDIUM", "HIGH"
    complexity_score: float  # 0.0 to 1.0
    token_count: int
    reasoning_depth_detected: bool
    tool_interaction_count: int
    intent_tag: str


@dataclass(slots=True, frozen=True)
class RoutingDecision:
    """Tier 2: Model routing assignment and fallback specifications."""

    assigned_tier: str
    primary_model: str
    fallback_chain: list[str]
    estimated_cost_per_1k_tokens: float
    reasoning_budget: str  # "OFF", "LOW", "MEDIUM", "HIGH"


@dataclass(slots=True)
class ExecutionFallbackResult:
    """Tier 3: Execution result after potential fallback chain execution."""

    successful_model: str
    attempts: int
    fallback_triggered: bool
    execution_trace: list[str]
    status: str  # "SUCCESS", "CIRCUIT_BREAKER_OPEN", "ALL_FALLBACKS_EXHAUSTED"


class DynamicModelRouter:
    """Orchestrates 3-tier dynamic model switching, routing, and fallbacks."""

    MODEL_MATRIX: dict[str, dict[str, Any]] = {
        "LOW": {
            "primary": "gemini-2.5-flash",
            "fallbacks": ["claude-3-5-haiku", "gpt-4o-mini"],
            "cost_per_1k": 0.00015,
            "reasoning_budget": "OFF",
        },
        "MEDIUM": {
            "primary": "claude-3-7-sonnet",
            "fallbacks": ["gemini-2.5-flash", "gpt-4o"],
            "cost_per_1k": 0.003,
            "reasoning_budget": "LOW",
        },
        "HIGH": {
            "primary": "claude-3-7-sonnet-thinking",
            "fallbacks": ["gemini-3.8-flash-high", "o3-mini"],
            "cost_per_1k": 0.015,
            "reasoning_budget": "HIGH",
        },
    }

    REASONING_KEYWORDS = {
        "prove", "theorem", "refactor", "counterfactual", "causal", "deduce",
        "simulate", "optimize", "algebra", "calculus", "architectural", "invariant"
    }

    @classmethod
    def analyze_complexity(cls, prompt: str, candidate_tools: list[str] | None = None) -> ComplexityScore:
        """Tier 1: Analyze prompt length, intent keywords, and tool requirements."""
        tools = candidate_tools or []
        words = prompt.lower().split()
        token_estimate = max(1, int(len(prompt) / 4))

        # Check for deep reasoning indicators
        matched_reasoning = [k for k in cls.REASONING_KEYWORDS if k in words]
        has_reasoning = len(matched_reasoning) > 0
        tool_count = len(tools)

        score = 0.0
        # Token factor
        if token_estimate > 2000:
            score += 0.4
        elif token_estimate > 600:
            score += 0.2

        # Reasoning factor
        if len(matched_reasoning) >= 2:
            score += 0.5
        elif len(matched_reasoning) == 1:
            score += 0.35

        # Tool factor
        if tool_count > 5:
            score += 0.3
        elif tool_count > 0:
            score += 0.15

        score = min(1.0, score)

        if score >= 0.55:
            tier = "HIGH"
            intent = "deep_reasoning_and_composition"
        elif score >= 0.25:
            tier = "MEDIUM"
            intent = "tool_orchestration_or_multi_step"
        else:
            tier = "LOW"
            intent = "routine_retrieval_or_extraction"

        return ComplexityScore(
            tier=tier,
            complexity_score=round(score, 2),
            token_count=token_estimate,
            reasoning_depth_detected=has_reasoning,
            tool_interaction_count=tool_count,
            intent_tag=intent,
        )

    @classmethod
    def route_model(cls, complexity: ComplexityScore, cost_ceiling: float = 1.0) -> RoutingDecision:
        """Tier 2: Map complexity score to optimal model tier within cost constraints."""
        target_tier = complexity.tier

        # Downgrade if cost ceiling is strictly restrictive
        if cost_ceiling < 0.001 and target_tier == "HIGH":
            target_tier = "LOW"
        elif cost_ceiling < 0.005 and target_tier == "HIGH":
            target_tier = "MEDIUM"

        spec = cls.MODEL_MATRIX[target_tier]

        return RoutingDecision(
            assigned_tier=target_tier,
            primary_model=spec["primary"],
            fallback_chain=spec["fallbacks"],
            estimated_cost_per_1k_tokens=spec["cost_per_1k"],
            reasoning_budget=spec["reasoning_budget"],
        )

    @classmethod
    def simulate_fallback_chain(
        cls,
        decision: RoutingDecision,
        failing_providers: set[str] | None = None,
        max_retries: int = 3,
    ) -> ExecutionFallbackResult:
        """Tier 3: Execute model call with automated fallback rollover and circuit breaker."""
        failures = failing_providers or set()
        trace: list[str] = []
        candidates = [decision.primary_model] + decision.fallback_chain

        attempts = 0
        for model in candidates:
            attempts += 1
            if attempts > max_retries:
                trace.append(f"Exceeded max retries ({max_retries}); circuit breaker tripped.")
                return ExecutionFallbackResult(
                    successful_model="",
                    attempts=attempts,
                    fallback_triggered=True,
                    execution_trace=trace,
                    status="CIRCUIT_BREAKER_OPEN",
                )

            if model in failures:
                trace.append(f"Model {model} failed (HTTP 429/503/Timeout). Falling back to next provider...")
                continue

            trace.append(f"Model {model} succeeded on attempt {attempts}.")
            return ExecutionFallbackResult(
                successful_model=model,
                attempts=attempts,
                fallback_triggered=(model != decision.primary_model),
                execution_trace=trace,
                status="SUCCESS",
            )

        trace.append("All candidates in fallback chain exhausted.")
        return ExecutionFallbackResult(
            successful_model="",
            attempts=attempts,
            fallback_triggered=True,
            execution_trace=trace,
            status="ALL_FALLBACKS_EXHAUSTED",
        )
