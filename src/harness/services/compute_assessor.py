"""Compute & Model Assessor Subsystem.

Provides multi-dimensional complexity scoring, reasoning budget calibration,
provider-specific payload synthesis (Gemini, Claude, OpenAI, DeepSeek, LiteLLM),
and interactive visual review brief generation.
"""

from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

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
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "high_factors": self.high_factors,
            "low_factors": self.low_factors,
            "detected_keywords": self.detected_keywords,
            "files_evaluated": self.files_evaluated,
            "is_architectural": self.is_architectural,
            "is_debugging": self.is_debugging,
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
        return "\n".join(lines)


class DimensionalScorer:
    """Evaluates task surface across 5 orthogonal complexity dimensions."""

    HIGH_KEYWORDS = {
        "refactor", "architect", "deepen", "concurrency", "race condition",
        "deadlock", "dag", "isnad", "security", "threat model", "migration",
        "multi-file", "ast", "inversion of control", "topological", "consensus",
        "distributed", "sandbox", "metaclass", "protocol", "kernel", "cryptography"
    }

    LOW_KEYWORDS = {
        "format", "lint", "regex", "boilerplate", "docstring", "typo",
        "print", "rename", "capitalize", "json schema", "convert case",
        "comment", "whitespace", "markdown", "sort imports"
    }

    CONCURRENCY_KEYWORDS = {
        "asyncio", "thread", "concurrency", "lock", "mutex", "deadlock",
        "race condition", "event loop", "parallel", "semaphore"
    }

    DEPTH_KEYWORDS = {
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
    ) -> tuple[ComplexityVector, AssessmentTrace]:
        """Compute dimensional scores, vector composite, and explainability trace."""
        prompt_lower = prompt.lower()
        
        detected_high = [kw for kw in cls.HIGH_KEYWORDS if kw in prompt_lower]
        detected_low = [kw for kw in cls.LOW_KEYWORDS if kw in prompt_lower]
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

        # Weighted Composite Score
        # Ambiguity (25%), Span (25%), Depth (20%), Rigor (20%), Concurrency (10%)
        composite = (
            (ambiguity * 0.25)
            + (span * 0.25)
            + (depth * 0.20)
            + (rigor * 0.20)
            + (concurrency * 0.10)
        )

        # Classify Level
        if is_architecture or files_count > 3 or (detected_high and (is_debugging or files_count > 1)) or composite >= 0.65:
            level = "High"
        elif (detected_low and not detected_high and files_count <= 1 and not is_debugging and composite < 0.35):
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
            notes=f"Composite score {composite:.2f} classified into {level} complexity tier.",
        )

        return vector, trace


class ProviderReasoningAdapter:
    """Synthesizes vendor-specific LLM parameters for reasoning configurations."""

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
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        model_lower = model_name.lower()

        # Google Gemini 3.7 / 2.0
        if "gemini" in model_lower:
            if thinking_level == ThinkingBudget.OFF:
                payload["thinking_config"] = {"thinking_budget": 0}
            elif thinking_level == ThinkingBudget.LOW:
                payload["thinking_config"] = {"thinking_budget": 1024}
            elif thinking_level == ThinkingBudget.MEDIUM:
                payload["thinking_config"] = {"thinking_budget": max(4096, budget_tokens)}
            elif thinking_level == ThinkingBudget.HIGH:
                payload["thinking_config"] = {"thinking_budget": max(16384, budget_tokens)}
            payload["thinking_budget"] = thinking_level.value

        # Anthropic Claude 3.7 / 3.5
        elif "claude" in model_lower:
            if thinking_level != ThinkingBudget.OFF and budget_tokens > 0:
                payload["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": budget_tokens,
                }
                # Anthropic requires max_tokens > budget_tokens
                if not max_tokens or max_tokens <= budget_tokens:
                    payload["max_tokens"] = budget_tokens + 4096
            else:
                payload["thinking"] = {"type": "disabled"}

        # OpenAI o1, o3-mini, gpt-4o
        elif "o1" in model_lower or "o3" in model_lower:
            effort_map = {
                ThinkingBudget.HIGH: "high",
                ThinkingBudget.MEDIUM: "medium",
                ThinkingBudget.LOW: "low",
                ThinkingBudget.OFF: "low",
            }
            payload["reasoning_effort"] = effort_map.get(thinking_level, "medium")
        
        # DeepSeek-R1 / Open-Weights reasoning models
        elif "deepseek-r1" in model_lower or "r1" in model_lower:
            payload["extra_body"] = {"reasoning_effort": thinking_level.value}
            payload["budget_tokens"] = budget_tokens

        # Generic LiteLLM extra kwargs
        payload["reasoning_effort"] = thinking_level.value
        return payload


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
          <span class="text-xs text-gray-400 font-mono">Stage 3 Visual Brief</span>
        </div>
        <h1 class="text-2xl font-bold text-white mt-1">{task_title}</h1>
        <p class="text-xs text-gray-400">Calibrated for Gemini 3.7 Flash, Claude 3.7 Sonnet, OpenAI o-series</p>
      </div>
      <div class="text-right">
        <span class="bg-{'green-900/80 text-green-300 border-green-700' if assessment.complexity == 'Low' else 'blue-900/80 text-blue-300 border-blue-700' if assessment.complexity == 'Medium' else 'purple-900/80 text-purple-300 border-purple-700'} text-xs px-3 py-1.5 rounded-full font-mono font-bold border">
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
        <div class="text-xs text-gray-400">Composite Score</div>
        <div class="text-2xl font-extrabold text-white mt-1 text-purple-400 font-mono">{vector.composite_score:.2f} / 1.00</div>
        <div class="text-xs text-gray-400 mt-2">Evaluated {trace.files_evaluated} files • Arch: {trace.is_architectural}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl">
        <div class="text-xs text-gray-400">Alternative &amp; Peer Models</div>
        <div class="flex flex-wrap gap-1.5 mt-2">
          {alt_models_html}
        </div>
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
    ) -> ComputeAssessment:
        """Classify task complexity and return a calibrated compute recommendation."""
        # 1. Check manual overrides
        if override_tier == ModelTier.HIGH_REASONING:
            vector = ComplexityVector(composite_score=0.9, level="High")
            trace = AssessmentTrace(notes="Manual override set to High Reasoning tier.")
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
            )
        elif override_tier == ModelTier.FAST_MECHANICAL:
            vector = ComplexityVector(composite_score=0.1, level="Low")
            trace = AssessmentTrace(notes="Manual override set to Fast Mechanical tier.")
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
            )
        elif override_tier == ModelTier.STANDARD_AGENTIC:
            vector = ComplexityVector(composite_score=0.5, level="Medium")
            trace = AssessmentTrace(notes="Manual override set to Standard Agentic tier.")
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
            )

        # 2. Dimensional scoring
        vector, trace = DimensionalScorer.evaluate(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
        )

        if vector.level == "High":
            return ComputeAssessment(
                complexity="High",
                model_tier=ModelTier.HIGH_REASONING,
                thinking_level=ThinkingBudget.HIGH,
                recommended_model="gemini-3.7-flash",
                budget_tokens=16384,
                alternative_models=["claude-3-7-sonnet", "o3-mini", "deepseek-r1"],
                reasoning="High complexity: cross-module scope, structural ambiguity, or architectural constraints.",
                vector=vector,
                trace=trace,
            )
        elif vector.level == "Low":
            return ComputeAssessment(
                complexity="Low",
                model_tier=ModelTier.FAST_MECHANICAL,
                thinking_level=ThinkingBudget.OFF,
                recommended_model="gemini-2.0-flash",
                budget_tokens=0,
                alternative_models=["gpt-4o-mini", "claude-3-5-haiku", "mistral-small"],
                reasoning="Low complexity: mechanical syntax, parsing, or linear boilerplate.",
                vector=vector,
                trace=trace,
            )
        else:
            return ComputeAssessment(
                complexity="Medium",
                model_tier=ModelTier.STANDARD_AGENTIC,
                thinking_level=ThinkingBudget.MEDIUM,
                recommended_model="gemini-3.7-flash",
                budget_tokens=4096,
                alternative_models=["gpt-4o", "claude-3-5-sonnet", "deepseek-v3"],
                reasoning="Medium complexity: standard single-module feature implementation or unit test creation.",
                vector=vector,
                trace=trace,
            )

    @classmethod
    def generate_visual_brief(
        cls,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        task_title: str = "Compute Assessment",
    ) -> str:
        """Assess prompt and generate an interactive HTML visual brief in %TEMP%."""
        assessment = cls.assess(
            prompt,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
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
