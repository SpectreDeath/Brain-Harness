"""Compute & Model Assessor Subsystem.

Provides multi-dimensional complexity scoring, reasoning budget calibration,
pluggable provider parameter synthesis (Gemini, Claude, OpenAI, DeepSeek, Ollama, LiteLLM),
token economics & latency estimation, and interactive visual review brief generation.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, HarnessEvent, compute_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class ThinkingBudget(str, Enum):
    """Reasoning effort / thinking budget levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OFF = "off"


class ModelTier(str, Enum):
    """Classification of LLM capabilities and execution tiers."""

    HIGH_REASONING = "high_reasoning"
    STANDARD_AGENTIC = "standard_agentic"
    FAST_MECHANICAL = "fast_mechanical"


class ComplexityDimension(str, Enum):
    """Orthogonal dimensions of task complexity."""

    AMBIGUITY = "ambiguity"
    SPAN = "span"
    DEPTH = "depth"
    RIGOR = "rigor"
    CONCURRENCY = "concurrency"


class ScoringProfileName(str, Enum):
    """Pre-configured scoring profile presets."""

    BALANCED = "balanced"
    REASONING_HEAVY = "reasoning_heavy"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"


@dataclass
class ScoringProfile:
    """Configurable weights and threshold rules for dimensional complexity scoring."""

    name: str = "balanced"
    ambiguity_weight: float = 0.25
    span_weight: float = 0.25
    depth_weight: float = 0.20
    rigor_weight: float = 0.20
    concurrency_weight: float = 0.10
    high_threshold: float = 0.65
    low_threshold: float = 0.35
    custom_high_keywords: set[str] = field(default_factory=set)
    custom_low_keywords: set[str] = field(default_factory=set)

    @classmethod
    def get_preset(cls, preset: ScoringProfileName | str) -> ScoringProfile:
        """Retrieve standard pre-configured scoring profile preset."""
        p_name = preset.value if isinstance(preset, ScoringProfileName) else str(preset).lower()
        if p_name == "reasoning_heavy":
            return cls(
                name="reasoning_heavy",
                ambiguity_weight=0.30,
                span_weight=0.25,
                depth_weight=0.25,
                rigor_weight=0.15,
                concurrency_weight=0.05,
                high_threshold=0.55,
                low_threshold=0.25,
            )
        elif p_name == "cost_optimized":
            return cls(
                name="cost_optimized",
                ambiguity_weight=0.20,
                span_weight=0.20,
                depth_weight=0.20,
                rigor_weight=0.20,
                concurrency_weight=0.20,
                high_threshold=0.75,
                low_threshold=0.45,
            )
        elif p_name == "latency_optimized":
            return cls(
                name="latency_optimized",
                ambiguity_weight=0.20,
                span_weight=0.20,
                depth_weight=0.20,
                rigor_weight=0.20,
                concurrency_weight=0.20,
                high_threshold=0.80,
                low_threshold=0.50,
            )
        return cls(name="balanced")


@dataclass
class ModelPricingRecord:
    """Pricing and latency metrics for a specific model."""

    input_per_m: float = 0.50
    output_per_m: float = 1.50
    p50_s: float = 1.5
    p95_s: float = 4.0
    thinking_p50_s: float = 4.0
    thinking_p95_s: float = 10.0


class ModelPricingCatalog:
    """Extensible catalog and matching database for model pricing and latency."""

    DEFAULT_PRICING: dict[str, dict[str, Any]] = {
        "gemini-3.7-flash": {
            "input_per_m": 0.15,
            "output_per_m": 0.60,
            "p50_s": 1.2,
            "p95_s": 3.5,
            "thinking_p50_s": 4.5,
            "thinking_p95_s": 12.0,
        },
        "gemini-2.0-flash": {
            "input_per_m": 0.10,
            "output_per_m": 0.40,
            "p50_s": 0.6,
            "p95_s": 1.8,
            "thinking_p50_s": 1.5,
            "thinking_p95_s": 3.5,
        },
        "gemini-1.5-pro": {
            "input_per_m": 1.25,
            "output_per_m": 5.00,
            "p50_s": 2.0,
            "p95_s": 5.5,
            "thinking_p50_s": 5.0,
            "thinking_p95_s": 14.0,
        },
        "claude-3-7-sonnet": {
            "input_per_m": 3.00,
            "output_per_m": 15.00,
            "p50_s": 3.0,
            "p95_s": 8.0,
            "thinking_p50_s": 8.0,
            "thinking_p95_s": 25.0,
        },
        "claude-3-5-sonnet": {
            "input_per_m": 3.00,
            "output_per_m": 15.00,
            "p50_s": 2.5,
            "p95_s": 6.0,
            "thinking_p50_s": 2.5,
            "thinking_p95_s": 6.0,
        },
        "claude-3-5-haiku": {
            "input_per_m": 0.80,
            "output_per_m": 4.00,
            "p50_s": 0.8,
            "p95_s": 2.0,
            "thinking_p50_s": 0.8,
            "thinking_p95_s": 2.0,
        },
        "o3-mini": {
            "input_per_m": 1.10,
            "output_per_m": 4.40,
            "p50_s": 4.0,
            "p95_s": 15.0,
            "thinking_p50_s": 7.0,
            "thinking_p95_s": 20.0,
        },
        "o1": {
            "input_per_m": 15.00,
            "output_per_m": 60.00,
            "p50_s": 6.0,
            "p95_s": 25.0,
            "thinking_p50_s": 10.0,
            "thinking_p95_s": 35.0,
        },
        "gpt-4o": {
            "input_per_m": 2.50,
            "output_per_m": 10.00,
            "p50_s": 2.0,
            "p95_s": 5.0,
            "thinking_p50_s": 2.0,
            "thinking_p95_s": 5.0,
        },
        "gpt-4o-mini": {
            "input_per_m": 0.15,
            "output_per_m": 0.60,
            "p50_s": 0.7,
            "p95_s": 1.9,
            "thinking_p50_s": 0.7,
            "thinking_p95_s": 1.9,
        },
        "deepseek-r1": {
            "input_per_m": 0.55,
            "output_per_m": 2.19,
            "p50_s": 5.0,
            "p95_s": 18.0,
            "thinking_p50_s": 8.0,
            "thinking_p95_s": 22.0,
        },
        "deepseek-v3": {
            "input_per_m": 0.14,
            "output_per_m": 0.28,
            "p50_s": 1.5,
            "p95_s": 4.0,
            "thinking_p50_s": 1.5,
            "thinking_p95_s": 4.0,
        },
        "ollama": {
            "input_per_m": 0.00,
            "output_per_m": 0.00,
            "p50_s": 1.0,
            "p95_s": 3.0,
            "thinking_p50_s": 3.0,
            "thinking_p95_s": 8.0,
        },
    }

    def __init__(self) -> None:
        self._pricing: dict[str, ModelPricingRecord] = {}
        for k, v in self.DEFAULT_PRICING.items():
            self._pricing[k] = ModelPricingRecord(**v)

    def register(self, model_name: str, record: ModelPricingRecord | dict[str, Any]) -> None:
        """Register or override pricing for a specific model identifier."""
        if isinstance(record, dict):
            record = ModelPricingRecord(**record)
        self._pricing[model_name.lower()] = record

    def get(self, model_name: str) -> ModelPricingRecord:
        """Resolve pricing metrics for model name via direct match, substring, or local fallback."""
        m = model_name.lower()
        if m in self._pricing:
            return self._pricing[m]
        for k, v in self._pricing.items():
            if k in m or m in k:
                return v
        if any(prefix in m for prefix in ("ollama", "local", "qwen", "llama", "mistral")):
            return self._pricing.get("ollama", ModelPricingRecord(input_per_m=0.0, output_per_m=0.0, p50_s=1.0, p95_s=3.0, thinking_p50_s=3.0, thinking_p95_s=8.0))
        return ModelPricingRecord()

    @property
    def all_models(self) -> list[str]:
        return list(self._pricing.keys())


GLOBAL_PRICING_CATALOG = ModelPricingCatalog()


@dataclass
class ComputeEconomics:
    """Estimated token cost and latency projection for a model configuration."""

    cost_per_million_input_usd: float = 0.0
    cost_per_million_output_usd: float = 0.0
    expected_latency_p50_seconds: float = 1.0
    expected_latency_p95_seconds: float = 3.0
    estimated_query_cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_per_million_input_usd": self.cost_per_million_input_usd,
            "cost_per_million_output_usd": self.cost_per_million_output_usd,
            "expected_latency_p50_seconds": self.expected_latency_p50_seconds,
            "expected_latency_p95_seconds": self.expected_latency_p95_seconds,
            "estimated_query_cost_usd": round(self.estimated_query_cost_usd, 6),
        }


class ComputeEconomicsEstimator:
    """Authoritative pricing and latency modeling database across model tiers."""

    PRICING_TABLE: dict[str, dict[str, Any]] = ModelPricingCatalog.DEFAULT_PRICING

    @classmethod
    def estimate(
        cls,
        model: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        estimated_input_tokens: int = 2000,
        estimated_output_tokens: int = 1500,
        catalog: ModelPricingCatalog | None = None,
    ) -> ComputeEconomics:
        """Calculate projected token costs and latency profile."""
        active_catalog = catalog or GLOBAL_PRICING_CATALOG
        pricing = active_catalog.get(model)

        is_thinking = thinking_level not in (ThinkingBudget.OFF, ThinkingBudget.LOW) or budget_tokens > 2048
        p50 = pricing.thinking_p50_s if is_thinking else pricing.p50_s
        p95 = pricing.thinking_p95_s if is_thinking else pricing.p95_s

        total_output_tokens = estimated_output_tokens + (budget_tokens if is_thinking else 0)
        cost_input = (estimated_input_tokens / 1_000_000.0) * pricing.input_per_m
        cost_output = (total_output_tokens / 1_000_000.0) * pricing.output_per_m
        query_cost = cost_input + cost_output

        return ComputeEconomics(
            cost_per_million_input_usd=pricing.input_per_m,
            cost_per_million_output_usd=pricing.output_per_m,
            expected_latency_p50_seconds=p50,
            expected_latency_p95_seconds=p95,
            estimated_query_cost_usd=query_cost,
        )


class ComputeAssessedEvent(BaseModel):
    """Typed Pydantic telemetry event for compute assessment audit logs."""

    complexity: str
    model_tier: str
    recommended_model: str
    budget_tokens: int
    composite_score: float
    estimated_cost_usd: float
    timestamp: float = Field(default_factory=time.time)


@dataclass
class ComplexityVector:
    """Multi-dimensional scoring vector evaluating task surface complexity."""

    ambiguity_score: float = 0.0
    span_score: float = 0.0
    depth_score: float = 0.0
    rigor_score: float = 0.0
    concurrency_score: float = 0.0
    composite_score: float = 0.0
    level: str = "Medium"  # "High", "Medium", "Low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ambiguity": round(self.ambiguity_score, 2),
            "span": round(self.span_score, 2),
            "depth": round(self.depth_score, 2),
            "rigor": round(self.rigor_score, 2),
            "concurrency": round(self.concurrency_score, 2),
            "composite": round(self.composite_score, 2),
            "level": self.level,
        }


@dataclass
class AssessmentTrace:
    """Explainability trace detailing factors influencing the compute assessment."""

    high_factors: list[str] = field(default_factory=list)
    low_factors: list[str] = field(default_factory=list)
    detected_keywords: list[str] = field(default_factory=list)
    files_evaluated: int = 1
    is_architectural: bool = False
    is_debugging: bool = False
    profile_used: str = "balanced"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "high_factors": self.high_factors,
            "low_factors": self.low_factors,
            "detected_keywords": self.detected_keywords,
            "files_evaluated": self.files_evaluated,
            "is_architectural": self.is_architectural,
            "is_debugging": self.is_debugging,
            "profile_used": self.profile_used,
            "notes": self.notes,
        }


@dataclass
class ComputeAssessment:
    """Structured compute allocation and model routing recommendation."""

    complexity: str  # "High", "Medium", "Low"
    model_tier: ModelTier
    thinking_level: ThinkingBudget
    recommended_model: str
    budget_tokens: int
    alternative_models: list[str] = field(default_factory=list)
    reasoning: str = ""
    vector: ComplexityVector | None = None
    trace: AssessmentTrace | None = None
    economics: ComputeEconomics | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "complexity": self.complexity,
            "model_tier": self.model_tier.value,
            "thinking_level": self.thinking_level.value,
            "recommended_model": self.recommended_model,
            "budget_tokens": self.budget_tokens,
            "alternative_models": self.alternative_models,
            "reasoning": self.reasoning,
        }
        if self.vector:
            result["vector"] = self.vector.to_dict()
        if self.trace:
            result["trace"] = self.trace.to_dict()
        if self.economics:
            result["economics"] = self.economics.to_dict()
        return result

    def format_recommendation_block(self) -> str:
        """Format the canonical Markdown compute recommendation block."""
        alt_str = " | ".join(self.alternative_models)
        lines = [
            "### [Compute Recommendation Block]",
            f"- **Complexity Assessment**: `{self.complexity}` (Tier: `{self.model_tier.value}`)",
            f"- **Primary Recommendation**: `{self.recommended_model}` (Thinking Level: `{self.thinking_level.value.upper()}`)",
            f"- **Reasoning Budget Tokens**: `~{self.budget_tokens:,} tokens`",
            f"- **Alternative / Peer Models**: `{alt_str}`",
            f"- **Rationale**: {self.reasoning}",
        ]
        if self.vector:
            lines.append(
                f"- **Vector Breakdown**: Ambiguity: {self.vector.ambiguity_score:.1f}, "
                f"Span: {self.vector.span_score:.1f}, Depth: {self.vector.depth_score:.1f}, "
                f"Rigor: {self.vector.rigor_score:.1f}, Concurrency: {self.vector.concurrency_score:.1f}"
            )
        if self.economics:
            lines.append(
                f"- **Economics Projection**: ~${self.economics.estimated_query_cost_usd:.4f} est. cost | "
                f"Latency: p50 ~{self.economics.expected_latency_p50_seconds:.1f}s, p95 ~{self.economics.expected_latency_p95_seconds:.1f}s"
            )
        return "\n".join(lines)


class DimensionalScorer:
    """Evaluates task surface across 5 orthogonal complexity dimensions with configurable profiles."""

    HIGH_KEYWORDS: set[str] = {
        "refactor", "architect", "deepen", "concurrency", "race condition",
        "deadlock", "dag", "isnad", "security", "threat model", "migration",
        "multi-file", "ast", "inversion of control", "topological", "consensus",
        "distributed", "sandbox", "metaclass", "protocol", "kernel", "cryptography"
    }

    LOW_KEYWORDS: set[str] = {
        "format", "lint", "regex", "boilerplate", "docstring", "typo",
        "print", "rename", "capitalize", "json schema", "convert case",
        "comment", "whitespace", "markdown", "sort imports"
    }

    CONCURRENCY_KEYWORDS: set[str] = {
        "asyncio", "thread", "concurrency", "lock", "mutex", "deadlock",
        "race condition", "event loop", "parallel", "semaphore"
    }

    DEPTH_KEYWORDS: set[str] = {
        "ast", "parser", "type system", "topological", "compiler", "dag",
        "bytecode", "algorithm", "recursive", "optimization", "graph"
    }

    @classmethod
    def evaluate(
        cls,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> tuple[ComplexityVector, AssessmentTrace]:
        """Compute dimensional scores, vector composite, and explainability trace."""
        active_profile: ScoringProfile
        if isinstance(profile, ScoringProfile):
            active_profile = profile
        elif profile:
            active_profile = ScoringProfile.get_preset(profile)
        else:
            active_profile = ScoringProfile.get_preset(ScoringProfileName.BALANCED)

        prompt_lower = prompt.lower()
        
        all_high_kw = cls.HIGH_KEYWORDS | active_profile.custom_high_keywords
        all_low_kw = cls.LOW_KEYWORDS | active_profile.custom_low_keywords

        detected_high = [kw for kw in all_high_kw if kw in prompt_lower]
        detected_low = [kw for kw in all_low_kw if kw in prompt_lower]
        detected_concurrency = [kw for kw in cls.CONCURRENCY_KEYWORDS if kw in prompt_lower]
        detected_depth = [kw for kw in cls.DEPTH_KEYWORDS if kw in prompt_lower]

        # 1. Ambiguity Score (0.0 to 1.0)
        ambiguity = 0.3
        if is_debugging:
            ambiguity += 0.4
        if "design" in prompt_lower or "architect" in prompt_lower or "explore" in prompt_lower:
            ambiguity += 0.3
        if detected_low and not detected_high:
            ambiguity = max(0.1, ambiguity - 0.2)
        ambiguity = min(1.0, max(0.0, ambiguity))

        # 2. Span Score (0.0 to 1.0) based on files and multi-module references
        span = 0.2
        if files_count > 3:
            span = 0.9
        elif files_count > 1:
            span = 0.6
        if "multi-file" in prompt_lower or "across" in prompt_lower or "subsystem" in prompt_lower:
            span = min(1.0, span + 0.3)

        # 3. Depth Score (0.0 to 1.0)
        depth = 0.3
        if detected_depth:
            depth += 0.4
        if is_architecture:
            depth += 0.3
        if "kernel" in prompt_lower or "core" in prompt_lower:
            depth += 0.2
        depth = min(1.0, max(0.0, depth))

        # 4. Rigor Score (0.0 to 1.0)
        rigor = 0.3
        if "migration" in prompt_lower or "persistent" in prompt_lower or "database" in prompt_lower:
            rigor += 0.4
        if "security" in prompt_lower or "audit" in prompt_lower or "isnad" in prompt_lower:
            rigor += 0.4
        if is_architecture:
            rigor += 0.2
        rigor = min(1.0, max(0.0, rigor))

        # 5. Concurrency Score (0.0 to 1.0)
        concurrency = 0.1
        if detected_concurrency:
            concurrency = min(1.0, 0.4 + (0.2 * len(detected_concurrency)))

        # Weighted Composite Score using active profile
        composite = (
            (ambiguity * active_profile.ambiguity_weight)
            + (span * active_profile.span_weight)
            + (depth * active_profile.depth_weight)
            + (rigor * active_profile.rigor_weight)
            + (concurrency * active_profile.concurrency_weight)
        )

        # Classify Level using profile thresholds
        if (
            is_architecture
            or files_count > 3
            or (detected_high and (is_debugging or files_count > 1))
            or composite >= active_profile.high_threshold
        ):
            level = "High"
        elif (
            detected_low
            and not detected_high
            and files_count <= 1
            and not is_architecture
            and not is_debugging
            and composite < active_profile.low_threshold
        ):
            level = "Low"
        else:
            level = "Medium"

        vector = ComplexityVector(
            ambiguity_score=ambiguity,
            span_score=span,
            depth_score=depth,
            rigor_score=rigor,
            concurrency_score=concurrency,
            composite_score=composite,
            level=level,
        )

        high_factors: list[str] = []
        if is_architecture:
            high_factors.append("Architectural refactoring flag enabled")
        if files_count > 3:
            high_factors.append(f"High multi-file footprint ({files_count} files)")
        if detected_high:
            high_factors.append(f"High-complexity keywords detected: {', '.join(detected_high)}")
        if is_debugging:
            high_factors.append("Debugging / diagnostic investigation flag enabled")

        low_factors: list[str] = []
        if detected_low:
            low_factors.append(f"Mechanical / low keywords detected: {', '.join(detected_low)}")
        if files_count <= 1 and not is_architecture and not is_debugging:
            low_factors.append("Confined single-file scope")

        trace = AssessmentTrace(
            high_factors=high_factors,
            low_factors=low_factors,
            detected_keywords=list(set(detected_high + detected_low)),
            files_evaluated=files_count,
            is_architectural=is_architecture,
            is_debugging=is_debugging,
            profile_used=active_profile.name,
            notes=f"Composite score {composite:.2f} classified into {level} complexity tier via '{active_profile.name}' profile.",
        )

        return vector, trace

    @classmethod
    def evaluate_conversation(
        cls,
        messages: list[Any],
        *,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> tuple[ComplexityVector, AssessmentTrace]:
        """Evaluate multi-turn conversation messages, detecting tool calls, context length, and algorithmic density."""
        combined_text_parts: list[str] = []
        tool_call_count = 0
        is_debugging = False
        is_architecture = False
        files_found: set[str] = set()

        for msg in messages:
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else str(msg))
            if isinstance(content, str):
                combined_text_parts.append(content)
                for word in content.split():
                    if "." in word and ("/" in word or "\\" in word or word.endswith((".py", ".ts", ".js", ".json", ".md", ".rs", ".go"))):
                        files_found.add(word)

            tc = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
            if tc:
                tool_call_count += len(tc)
            elif (
                getattr(msg, "tool_call_id", None)
                or (isinstance(msg, dict) and msg.get("tool_call_id"))
                or getattr(msg, "role", None) == "tool"
                or (isinstance(msg, dict) and msg.get("role") == "tool")
            ):
                tool_call_count += 1

        full_text = " ".join(combined_text_parts)
        prompt_lower = full_text.lower()
        if any(err_kw in prompt_lower for err_kw in ("error", "traceback", "exception", "failed", "bug", "deadlock", "race condition")):
            is_debugging = True
        if any(arch_kw in prompt_lower for arch_kw in ("architect", "refactor", "seam", "migration", "deepen", "kernel", "topological")):
            is_architecture = True

        files_count = max(1, len(files_found))
        vector, trace = cls.evaluate(
            full_text,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile,
        )

        if tool_call_count > 2:
            vector.depth_score = min(1.0, vector.depth_score + 0.15)
            vector.rigor_score = min(1.0, vector.rigor_score + 0.15)
            trace.high_factors.append(f"Active tool calling trajectory ({tool_call_count} tool calls)")

        trace.notes += f" Evaluated from {len(messages)} conversation messages with {tool_call_count} tool calls."
        return vector, trace



# ---------------------------------------------------------------------------
# Pluggable Provider Reasoning Transformers & Registry
# ---------------------------------------------------------------------------

class BaseProviderAdapter(ABC):
    """Abstract base adapter for vendor-specific reasoning and model parameter transforms."""

    @abstractmethod
    def can_handle(self, model_name: str) -> bool:
        """Return True if this adapter supports the specified model name."""

    @abstractmethod
    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize provider-specific payload parameters."""


class GeminiProviderAdapter(BaseProviderAdapter):
    """Transformer for Google Gemini reasoning and thinking configurations."""

    def can_handle(self, model_name: str) -> bool:
        return "gemini" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        if thinking_level == ThinkingBudget.OFF:
            payload["thinking_config"] = {"thinking_budget": 0}
        elif thinking_level == ThinkingBudget.LOW:
            payload["thinking_config"] = {"thinking_budget": 1024}
        elif thinking_level == ThinkingBudget.MEDIUM:
            payload["thinking_config"] = {"thinking_budget": max(4096, budget_tokens)}
        elif thinking_level == ThinkingBudget.HIGH:
            payload["thinking_config"] = {"thinking_budget": max(16384, budget_tokens)}

        payload["thinking_budget"] = thinking_level.value
        payload["reasoning_effort"] = thinking_level.value
        return payload


class ClaudeProviderAdapter(BaseProviderAdapter):
    """Transformer for Anthropic Claude extended thinking parameters."""

    def can_handle(self, model_name: str) -> bool:
        return "claude" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if thinking_level != ThinkingBudget.OFF and budget_tokens > 0:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget_tokens,
            }
            if not max_tokens or max_tokens <= budget_tokens:
                payload["max_tokens"] = budget_tokens + 4096
            else:
                payload["max_tokens"] = max_tokens
        else:
            payload["thinking"] = {"type": "disabled"}
            if max_tokens:
                payload["max_tokens"] = max_tokens

        payload["reasoning_effort"] = thinking_level.value
        return payload


class OpenAIProviderAdapter(BaseProviderAdapter):
    """Transformer for OpenAI o1 / o3-mini and GPT-4o reasoning models."""

    def can_handle(self, model_name: str) -> bool:
        m = model_name.lower()
        return "o1" in m or "o3" in m or "gpt-4" in m or "openai" in m

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        effort_map = {
            ThinkingBudget.HIGH: "high",
            ThinkingBudget.MEDIUM: "medium",
            ThinkingBudget.LOW: "low",
            ThinkingBudget.OFF: "low",
        }
        payload["reasoning_effort"] = effort_map.get(thinking_level, "medium")
        return payload


class DeepSeekProviderAdapter(BaseProviderAdapter):
    """Transformer for DeepSeek-R1 / DeepSeek-V3 reasoning configurations."""

    def can_handle(self, model_name: str) -> bool:
        return "deepseek" in model_name.lower() or "r1" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "extra_body": {"reasoning_effort": thinking_level.value},
            "budget_tokens": budget_tokens,
            "reasoning_effort": thinking_level.value,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload


class OllamaProviderAdapter(BaseProviderAdapter):
    """Transformer for Ollama and local LLM reasoning runtimes."""

    def can_handle(self, model_name: str) -> bool:
        return "ollama" in model_name.lower() or "qwen" in model_name.lower() or "llama" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "options": {"num_predict": max_tokens or (budget_tokens + 2048)},
            "reasoning_effort": thinking_level.value,
        }
        return payload


class FallbackLiteLLMAdapter(BaseProviderAdapter):
    """Fallback transformer for generic LiteLLM and OpenRouter models."""

    def can_handle(self, model_name: str) -> bool:
        return True

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "reasoning_effort": thinking_level.value,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload


class ProviderReasoningRegistry:
    """Authoritative registry of pluggable provider reasoning transformers."""

    def __init__(self) -> None:
        self._adapters: list[BaseProviderAdapter] = [
            GeminiProviderAdapter(),
            ClaudeProviderAdapter(),
            OpenAIProviderAdapter(),
            DeepSeekProviderAdapter(),
            OllamaProviderAdapter(),
            FallbackLiteLLMAdapter(),
        ]

    def register(self, adapter: BaseProviderAdapter, insert_front: bool = True) -> None:
        """Register a new custom provider adapter."""
        if insert_front:
            self._adapters.insert(0, adapter)
        else:
            self._adapters.insert(len(self._adapters) - 1, adapter)

    def get_adapter(self, model_name: str) -> BaseProviderAdapter:
        """Resolve the matching provider adapter for model name."""
        for adapter in self._adapters:
            if adapter.can_handle(model_name):
                return adapter
        return self._adapters[-1]

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize target provider payload via matched adapter."""
        adapter = self.get_adapter(model_name)
        return adapter.transform(
            model_name,
            thinking_level,
            budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# Global authoritative provider registry
_GLOBAL_PROVIDER_REGISTRY = ProviderReasoningRegistry()


class ProviderReasoningAdapter:
    """Facade for provider payload synthesis delegating to pluggable registry."""

    @classmethod
    def get_provider_payload(
        cls,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize exact API request dictionary for target provider model."""
        return _GLOBAL_PROVIDER_REGISTRY.transform(
            model_name,
            thinking_level,
            budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def register_adapter(cls, adapter: BaseProviderAdapter, insert_front: bool = True) -> None:
        """Register a custom provider adapter into the global registry."""
        _GLOBAL_PROVIDER_REGISTRY.register(adapter, insert_front=insert_front)


# ---------------------------------------------------------------------------
# Visual Brief Generator & Interactive Provider Studio
# ---------------------------------------------------------------------------

class ComputeVisualBriefGenerator:
    """Generates self-contained interactive dark-mode HTML briefs in %TEMP%."""

    @classmethod
    def render_to_temp(cls, assessment: ComputeAssessment, task_title: str = "Compute Assessment") -> str:
        """Render assessment to an HTML file in temp directory and return its path."""
        ts = int(time.time())
        temp_dir = tempfile.gettempdir()
        filename = f"compute-assessor-{ts}.html"
        filepath = os.path.join(temp_dir, filename)

        vector = assessment.vector or ComplexityVector(level=assessment.complexity)
        trace = assessment.trace or AssessmentTrace()
        econ = assessment.economics or ComputeEconomicsEstimator.estimate(
            assessment.recommended_model,
            assessment.thinking_level,
            assessment.budget_tokens,
        )

        alt_models_html = "".join(
            f'<span class="bg-[#21262d] text-gray-300 px-2 py-1 rounded text-xs border border-[#30363d]">{m}</span>'
            for m in assessment.alternative_models
        )

        high_factors_html = "".join(
            f'<li class="text-red-300 text-xs">• {f}</li>'
            for f in trace.high_factors
        ) or '<li class="text-gray-500 text-xs italic">No high complexity blockers detected</li>'

        low_factors_html = "".join(
            f'<li class="text-green-300 text-xs">• {f}</li>'
            for f in trace.low_factors
        ) or '<li class="text-gray-500 text-xs italic">Standard agentic baseline</li>'

        # Generate sample payloads for the interactive studio
        gemini_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("gemini-3.7-flash", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        claude_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("claude-3-7-sonnet", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        openai_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("o3-mini", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        deepseek_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("deepseek-r1", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )
        ollama_payload = json.dumps(
            ProviderReasoningAdapter.get_provider_payload("ollama/qwen2.5-coder:32b", assessment.thinking_level, assessment.budget_tokens),
            indent=2,
        )

        badge_bg = (
            "bg-green-900/80 text-green-300 border-green-700"
            if assessment.complexity == "Low"
            else "bg-blue-900/80 text-blue-300 border-blue-700"
            if assessment.complexity == "Medium"
            else "bg-purple-900/80 text-purple-300 border-purple-700"
        )

        html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compute & Model Assessor Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#0d1117',
        primaryColor: '#1f6feb',
        primaryTextColor: '#c9d1d9',
        primaryBorderColor: '#30363d',
        lineColor: '#58a6ff'
      }}
    }});

    const providerPayloads = {{
      gemini: {json.dumps(gemini_payload)},
      claude: {json.dumps(claude_payload)},
      openai: {json.dumps(openai_payload)},
      deepseek: {json.dumps(deepseek_payload)},
      ollama: {json.dumps(ollama_payload)}
    }};

    function selectTab(provider) {{
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.remove('border-blue-500', 'text-blue-400', 'bg-[#21262d]');
        b.classList.add('text-gray-400');
      }});
      const activeBtn = document.getElementById('tab-' + provider);
      if (activeBtn) {{
        activeBtn.classList.add('border-blue-500', 'text-blue-400', 'bg-[#21262d]');
        activeBtn.classList.remove('text-gray-400');
      }}
      const codeBlock = document.getElementById('payload-code');
      if (codeBlock && providerPayloads[provider]) {{
        codeBlock.textContent = providerPayloads[provider];
      }}
    }}

    function copyPayload() {{
      const codeBlock = document.getElementById('payload-code');
      if (codeBlock) {{
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {{
          const toast = document.getElementById('copy-toast');
          if (toast) {{
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 2000);
          }}
        }});
      }}
    }}
  </script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] font-sans antialiased min-h-screen p-6 md:p-10">
  <div class="max-w-5xl mx-auto space-y-6">
    
    <header class="border-b border-[#30363d] pb-4 flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-mono bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded border border-blue-700/50">
            COMPUTE ROUTER
          </span>
          <span class="text-xs text-gray-400 font-mono">Stage 3 Visual Brief • Reactive IoC</span>
        </div>
        <h1 class="text-2xl font-bold text-white mt-1">{task_title}</h1>
        <p class="text-xs text-gray-400">Calibrated for Gemini 3.7 Flash, Claude 3.7 Sonnet, OpenAI o-series</p>
      </div>
      <div class="text-right">
        <span class="{badge_bg} text-xs px-3 py-1.5 rounded-full font-mono font-bold border">
          TIER: {assessment.complexity.upper()} ({assessment.model_tier.value})
        </span>
      </div>
    </header>

    <!-- Recommendation Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Primary Recommended Model</div>
        <div class="text-lg font-bold text-white mt-1 text-blue-400 font-mono">{assessment.recommended_model}</div>
        <div class="text-xs text-gray-400 mt-2">Thinking Budget: <span class="text-white font-mono font-semibold">{assessment.thinking_level.value.upper()} (~{assessment.budget_tokens:,} tokens)</span></div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Composite Score &amp; Profile</div>
        <div class="text-2xl font-extrabold text-white mt-1 text-purple-400 font-mono">{vector.composite_score:.2f} / 1.00</div>
        <div class="text-xs text-gray-400 mt-2">Profile: <span class="text-purple-300 font-mono">{trace.profile_used}</span> • Files: {trace.files_evaluated}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Token Economics &amp; Latency</div>
        <div class="text-lg font-bold text-white mt-1 text-green-400 font-mono">~${econ.estimated_query_cost_usd:.4f}</div>
        <div class="text-xs text-gray-400 mt-2">p50: <span class="text-gray-200">{econ.expected_latency_p50_seconds:.1f}s</span> • p95: <span class="text-gray-200">{econ.expected_latency_p95_seconds:.1f}s</span></div>
      </div>
    </div>

    <!-- Complexity Vector & Decision DAG -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Vector Breakdown -->
      <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl space-y-4">
        <h3 class="text-sm font-bold text-white">5-Dimensional Complexity Vector</h3>
        <div class="space-y-2.5 font-mono text-xs">
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Solution Ambiguity</span>
              <span class="font-bold text-blue-400">{vector.ambiguity_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.ambiguity_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Context &amp; DAG Span</span>
              <span class="font-bold text-blue-400">{vector.span_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.span_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Algorithmic Depth</span>
              <span class="font-bold text-blue-400">{vector.depth_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.depth_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Execution Rigor</span>
              <span class="font-bold text-blue-400">{vector.rigor_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.rigor_score * 100)}%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-gray-300 mb-1">
              <span>Concurrency / Race Potential</span>
              <span class="font-bold text-blue-400">{vector.concurrency_score:.2f}</span>
            </div>
            <div class="w-full bg-[#0d1117] rounded-full h-2">
              <div class="bg-blue-500 h-2 rounded-full" style="width: {int(vector.concurrency_score * 100)}%"></div>
            </div>
          </div>
        </div>

        <div class="border-t border-[#30363d] pt-3">
          <div class="text-xs text-gray-400 font-semibold mb-1">Rationale:</div>
          <div class="text-xs text-gray-300 italic">{assessment.reasoning}</div>
        </div>
      </div>

      <!-- Decision DAG -->
      <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl">
        <h3 class="text-sm font-bold text-white mb-2">Routing Decision DAG</h3>
        <div class="mermaid">
graph TD
  Prompt["Task Prompt & Context"] --> Eval["DimensionalScorer (Composite: {vector.composite_score:.2f})"]
  Eval --> Decision{{"Tier: {assessment.complexity}"}}
  Decision -->|High| HighT["Gemini 3.7 Flash (Thinking: HIGH)<br/>Claude 3.7 Sonnet (>16k tok)"]
  Decision -->|Medium| MedT["Gemini 3.7 Flash (Thinking: MED)<br/>Claude 3.5 Sonnet / GPT-4o"]
  Decision -->|Low| LowT["Gemini 2.0 Flash (Thinking: OFF)<br/>GPT-4o-mini / Haiku"]
  
  style HighT fill:#28183d,stroke:#a371f7,stroke-width:1px,color:#fff
  style MedT fill:#092540,stroke:#58a6ff,stroke-width:1px,color:#fff
  style LowT fill:#0d3a1e,stroke:#238636,stroke-width:1px,color:#fff
        </div>
      </div>

    </div>

    <!-- Live Provider Payload Studio -->
    <div class="bg-[#161b22] border border-[#30363d] p-5 rounded-xl space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-bold text-white">Live Provider Payload Studio</h3>
          <span class="text-xs font-mono bg-purple-900/60 text-purple-300 px-2 py-0.5 rounded border border-purple-700/50">
            Multi-Provider Ready
          </span>
        </div>
        <button onclick="copyPayload()" class="text-xs bg-[#21262d] hover:bg-[#30363d] text-gray-200 px-2.5 py-1 rounded border border-[#30363d] flex items-center gap-1 transition">
          <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
          Copy JSON
        </button>
      </div>

      <!-- Tab Buttons -->
      <div class="flex border-b border-[#30363d] gap-2 text-xs font-mono">
        <button id="tab-gemini" onclick="selectTab('gemini')" class="tab-btn px-3 py-1.5 border-b-2 border-blue-500 text-blue-400 font-bold bg-[#21262d] rounded-t">Google Gemini</button>
        <button id="tab-claude" onclick="selectTab('claude')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">Anthropic Claude</button>
        <button id="tab-openai" onclick="selectTab('openai')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">OpenAI o-Series</button>
        <button id="tab-deepseek" onclick="selectTab('deepseek')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">DeepSeek</button>
        <button id="tab-ollama" onclick="selectTab('ollama')" class="tab-btn px-3 py-1.5 text-gray-400 hover:text-white rounded-t">Ollama / Local</button>
      </div>

      <!-- Code Box -->
      <div class="relative">
        <pre class="bg-[#0d1117] p-4 rounded-lg border border-[#30363d] text-xs font-mono text-gray-300 overflow-x-auto"><code id="payload-code">{gemini_payload}</code></pre>
        <div id="copy-toast" class="hidden absolute top-2 right-2 bg-green-900/90 text-green-300 border border-green-700 px-2 py-1 rounded text-xs font-mono">
          ✓ Copied to clipboard!
        </div>
      </div>
    </div>

    <!-- Factor Breakdown -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <h4 class="text-xs font-bold text-red-400 uppercase mb-2">High Complexity Indicators</h4>
        <ul class="space-y-1">
          {high_factors_html}
        </ul>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <h4 class="text-xs font-bold text-green-400 uppercase mb-2">Low Complexity Indicators</h4>
        <ul class="space-y-1">
          {low_factors_html}
        </ul>
      </div>
    </div>

    <footer class="border-t border-[#30363d] pt-4 text-xs text-gray-500 flex justify-between items-center font-mono">
      <div>Compute &amp; Model Assessor Engine • Brain Harness</div>
      <div>Generated at timestamp: {ts}</div>
    </footer>

  </div>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath


# ---------------------------------------------------------------------------
# Dynamic Trajectory Escalator & Multi-Attempt Ramping
# ---------------------------------------------------------------------------

@dataclass
class TrajectoryState:
    """State tracking for a task execution trajectory across attempts and errors."""

    attempt_count: int = 1
    error_count: int = 0
    consecutive_failures: int = 0
    total_tokens_consumed: int = 0
    is_escalated: bool = False
    original_tier: ModelTier = ModelTier.STANDARD_AGENTIC
    current_tier: ModelTier = ModelTier.STANDARD_AGENTIC
    history: list[dict[str, Any]] = field(default_factory=list)

    def record_attempt(self, success: bool, error: str | None = None, tokens_used: int = 0) -> None:
        """Record the outcome of an execution attempt."""
        self.attempt_count += 1
        self.total_tokens_consumed += tokens_used
        if not success:
            self.error_count += 1
            self.consecutive_failures += 1
            self.history.append({"attempt": self.attempt_count - 1, "status": "failed", "error": error})
        else:
            self.consecutive_failures = 0
            self.history.append({"attempt": self.attempt_count - 1, "status": "success"})


class DynamicTrajectoryEscalator:
    """Dynamic reasoning budget and model tier escalation engine for multi-attempt agent loops."""

    @classmethod
    def escalate(
        cls,
        base_assessment: ComputeAssessment,
        trajectory: TrajectoryState,
        *,
        catalog: ModelPricingCatalog | None = None,
    ) -> ComputeAssessment:
        """Dynamically escalate thinking budget and model tier based on trajectory failures/retries."""
        if trajectory.error_count == 0 and trajectory.consecutive_failures == 0 and trajectory.attempt_count <= 1:
            return base_assessment

        active_catalog = catalog or GLOBAL_PRICING_CATALOG
        tier = base_assessment.model_tier
        complexity = base_assessment.complexity
        budget = base_assessment.budget_tokens
        thinking = base_assessment.thinking_level
        rec_model = base_assessment.recommended_model
        alts = list(base_assessment.alternative_models)
        reason_notes: list[str] = []

        if trajectory.consecutive_failures >= 2 or (tier == ModelTier.HIGH_REASONING and trajectory.error_count >= 1):
            # Max thinking escalation
            complexity = "High"
            tier = ModelTier.HIGH_REASONING
            thinking = ThinkingBudget.HIGH
            rec_model = "gemini-3.7-flash"
            budget = max(budget * 2, 24576)
            alts = ["claude-3-7-sonnet", "o3-mini", "o1", "deepseek-r1"]
            reason_notes.append(f"Escalated to MAX reasoning budget ({budget:,} tokens) after {trajectory.consecutive_failures} consecutive failures.")
        elif trajectory.consecutive_failures >= 1 or trajectory.error_count >= 1 or trajectory.attempt_count > 1:
            if tier == ModelTier.FAST_MECHANICAL:
                complexity = "Medium"
                tier = ModelTier.STANDARD_AGENTIC
                thinking = ThinkingBudget.MEDIUM
                rec_model = "gemini-3.7-flash"
                budget = 4096
                alts = ["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"]
                reason_notes.append("Escalated from FAST_MECHANICAL to STANDARD_AGENTIC after error/retry.")
            elif tier == ModelTier.STANDARD_AGENTIC:
                complexity = "High"
                tier = ModelTier.HIGH_REASONING
                thinking = ThinkingBudget.HIGH
                rec_model = "gemini-3.7-flash"
                budget = 16384
                alts = ["claude-3-7-sonnet", "o3-mini", "deepseek-r1"]
                reason_notes.append("Escalated from STANDARD_AGENTIC to HIGH_REASONING after error/retry.")

        trajectory.is_escalated = True
        trajectory.current_tier = tier

        econ = ComputeEconomicsEstimator.estimate(rec_model, thinking, budget, catalog=active_catalog)
        escalated_vector = base_assessment.vector
        if escalated_vector:
            escalated_vector = ComplexityVector(
                ambiguity_score=min(1.0, escalated_vector.ambiguity_score + 0.2),
                span_score=escalated_vector.span_score,
                depth_score=min(1.0, escalated_vector.depth_score + 0.2),
                rigor_score=min(1.0, escalated_vector.rigor_score + 0.2),
                concurrency_score=escalated_vector.concurrency_score,
                composite_score=min(1.0, escalated_vector.composite_score + 0.2),
                level=complexity,
            )

        escalated_trace = base_assessment.trace
        if escalated_trace:
            escalated_trace = AssessmentTrace(
                high_factors=escalated_trace.high_factors + reason_notes,
                low_factors=escalated_trace.low_factors,
                detected_keywords=escalated_trace.detected_keywords,
                files_evaluated=escalated_trace.files_evaluated,
                is_architectural=escalated_trace.is_architectural,
                is_debugging=True,
                profile_used=escalated_trace.profile_used,
                notes=f"Trajectory escalated: {' '.join(reason_notes)}",
            )

        return ComputeAssessment(
            complexity=complexity,
            model_tier=tier,
            thinking_level=thinking,
            recommended_model=rec_model,
            budget_tokens=budget,
            alternative_models=alts,
            reasoning=base_assessment.reasoning + " " + " ".join(reason_notes),
            vector=escalated_vector,
            trace=escalated_trace,
            economics=econ,
        )

    @classmethod
    def allocate_tree_budget(
        cls,
        total_budget_tokens: int,
        branch_weights: list[float],
    ) -> list[int]:
        """Proportionally allocate reasoning token budget across swarm/tree branches."""
        if not branch_weights:
            return []
        total_weight = sum(branch_weights)
        if total_weight <= 0:
            equal_share = total_budget_tokens // len(branch_weights)
            return [equal_share] * len(branch_weights)
        return [int((w / total_weight) * total_budget_tokens) for w in branch_weights]


# ---------------------------------------------------------------------------
# Compute Router & Service
# ---------------------------------------------------------------------------

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
