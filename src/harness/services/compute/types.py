"""Types, enums, pricing catalog, and data structures for compute assessment."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
