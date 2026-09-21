---
name: dynamic-model-router
description: Architect, configure, and operate multi-provider dynamic LLM routing pipelines with sub-5ms heuristic complexity classification, declarative model matrices, and automated failover. Do not use for static single-model prompts or offline batch dataset labeling.
---

# Dynamic Model Router: Multi-Provider Switching & Resilient Failover Engine

`dynamic-model-router` is the cognitive and architectural engine for designing, deploying, and operating multi-provider AI model routing systems. Synthesized from Chidiebere Njoku's foundational literature (*How to Build AI Applications That Switch Models Automatically*, freeCodeCamp, 2026) and grounded in the Knowledge Vault ([ki_njoku_dynamic_model_routing](../../../.harness/knowledge/ki_njoku_dynamic_model_routing/summary.md)), this skill operationalizes dynamic model switching to eliminate single-point-of-failure API outages, curb token cost inflation, and enforce strict execution SLAs.

Relying on a single monolithic frontier model for every incoming request introduces severe production risks: upstream API downtime freezes end-user workflows, expensive reasoning models are wasted on trivial formatting tasks, and lightweight models fail on complex multi-step reasoning. `dynamic-model-router` enforces a decoupled 3-tier lifecycle: deterministic offline complexity profiling, declarative model matrix resolution, and resilient multi-provider failover.

Every dynamic model routing workflow executes this 5-stage progression:

```
[1. Offline Complexity Profiling] → [2. Declarative Matrix Resolution] → [3. Strict-Timeout Encasement] → [4. Automated Failover Execution] → [5. Schema Normalization & Telemetry]
```

See [CARD.md](CARD.md) for the companion summary card, stage reference matrix, and verification checklist.
Consult [../compute-model-assessor/SKILL.md](../compute-model-assessor/SKILL.md) for 5D compute assessment calibrations, [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for harness reliability mechanisms, and [../self-evaluating-ai-pipeline/SKILL.md](../self-evaluating-ai-pipeline/SKILL.md) for model evaluation gates.
Authoritative domain engine is co-located in [scripts/dynamic_model_router_engine.py](scripts/dynamic_model_router_engine.py) and elevated into the micro-kernel IoC service seam via [../../../plugins/agent_orchestration/dynamic_model_router/main.py](../../../plugins/agent_orchestration/dynamic_model_router/main.py).

---

## 1. Offline Complexity & Intent Profiling

Classify incoming prompts into discrete complexity tiers using deterministic, zero-LLM heuristics that execute in under 5 milliseconds:

1. **Deterministic Syntax & Length Heuristics**:
   - Never dispatch an LLM call to classify prompts; spending $0.005 and 500ms of network latency to route a prompt defeats the cost and throughput benefits of dynamic routing.
   - Profile incoming text strings using three fast syntactic checks:
     * *Code Block Fences*: Detect markdown code markers (` ``` `) signaling code generation, debugging, or syntax refactoring.
     * *Reasoning Regex Keywords*: Match high-cognitive intent tokens (`refactor`, `debug`, `algorithm`, `architecture`, `optimize`, `kernel`, `proof`, `analyze`).
     * *Word / Token Boundaries*: Split on whitespace to calculate raw length boundaries.
2. **Assign Task Complexity Tier**:
   - `TaskComplexity.SIMPLE`: Short factual prompts (< 80 words) containing zero code blocks and no reasoning keywords (e.g., FAQ lookups, classification, tone adjustment, one-sentence summaries).
   - `TaskComplexity.MEDIUM`: Moderate conversational prompts (80–300 words) requiring coherent structuring, entity extraction, or standard tool invocation.
   - `TaskComplexity.COMPLEX`: Heavy reasoning tasks containing code blocks, matching complex keywords, or exceeding 300 words in length.
3. **Complexity Engine Implementation**:

```python
from enum import Enum
import re

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class PromptAnalyzer:
    def __init__(self) -> None:
        self.complex_keywords = [
            r"\brefactor\b",
            r"\bdebug\b",
            r"\boptimize\b",
            r"\balgorithm\b",
            r"\barchitecture\b",
            r"\bconcurrency\b",
            r"\bkernel\b",
        ]

    def analyze_complexity(self, prompt: str) -> TaskComplexity:
        normalized = prompt.lower().strip()
        word_count = len(normalized.split())

        contains_code = "```" in prompt
        has_complex_keyword = any(
            re.search(pattern, normalized) for pattern in self.complex_keywords
        )

        if contains_code or has_complex_keyword or word_count > 300:
            return TaskComplexity.COMPLEX
        elif word_count > 80:
            return TaskComplexity.MEDIUM
        return TaskComplexity.SIMPLE
```

> **Completion criterion**: Prompt evaluated deterministically in $< 5\text{ ms}$ with zero network requests and categorized into `SIMPLE`, `MEDIUM`, or `COMPLEX`.

---

## 2. Declarative Model Routing Resolution

Map evaluated complexity tiers to primary and secondary fallback model configurations through a centralized, declarative routing table:

1. **Define Model Configuration Schema**:
   - Model configurations must declare both provider domain (e.g., `"openai"`, `"anthropic"`, `"gemini"`) and the specific versioned model identifier (e.g., `"gpt-4o-mini"`, `"claude-3-5-sonnet-20241022"`).
2. **Enforce the Provider Diversity Invariant**:
   - A primary model and its fallback must **never** share the same cloud provider infrastructure (`primary.provider != fallback.provider`).
   - Coupling a primary model (`gpt-4o`) to a same-vendor fallback (`gpt-4o-mini`) guarantees total outage during provider-wide API incidents, DNS outages, or auth service downtime.
3. **Route Against the 3-Tier Allocation Matrix**:
   - *Simple Tier*: Primary budget model (e.g., `openai / gpt-4o-mini`), backed by an alternative provider flash model (e.g., `anthropic / claude-3-5-haiku-20241022` or `gemini / gemini-2.5-flash`).
   - *Medium Tier*: Primary high-throughput model (e.g., `openai / gpt-4o-mini`), backed by balanced secondary (e.g., `anthropic / claude-3-5-haiku-20241022`).
   - *Complex Tier*: Primary frontier reasoning model (e.g., `anthropic / claude-3-5-sonnet-20241022`), backed by an alternative frontier reasoning model (e.g., `openai / gpt-4o` or `gemini / gemini-2.5-pro`).
4. **Router Implementation**:

```python
from pydantic import BaseModel

class ModelConfig(BaseModel):
    provider: str
    model_name: str

class ModelRouter:
    def __init__(self) -> None:
        self.routing_table: dict[TaskComplexity, dict[str, ModelConfig]] = {
            TaskComplexity.SIMPLE: {
                "primary": ModelConfig(provider="openai", model_name="gpt-4o-mini"),
                "fallback": ModelConfig(provider="anthropic", model_name="claude-3-5-haiku-20241022"),
            },
            TaskComplexity.MEDIUM: {
                "primary": ModelConfig(provider="openai", model_name="gpt-4o-mini"),
                "fallback": ModelConfig(provider="anthropic", model_name="claude-3-5-haiku-20241022"),
            },
            TaskComplexity.COMPLEX: {
                "primary": ModelConfig(provider="anthropic", model_name="claude-3-5-sonnet-20241022"),
                "fallback": ModelConfig(provider="openai", model_name="gpt-4o"),
            },
        }

    def get_models_for_tier(self, complexity: TaskComplexity) -> tuple[ModelConfig, ModelConfig]:
        config = self.routing_table[complexity]
        return config["primary"], config["fallback"]
```

> **Completion criterion**: Discrete `(primary, fallback)` tuple resolved from the routing table with strictly verified provider diversity.

---

## 3. Resilient Strict-Timeout Encasement

Encapsulate model provider calls behind unified abstraction bridges with aggressive, client-enforced socket timeouts:

1. **Tight Timeout Budgeting (5.0s – 10.0s)**:
   - Upstream model APIs frequently experience TCP hangs, threadpool stalls, or silent queuing during degradation rather than throwing clean immediate errors.
   - Relying on default SDK socket timeouts (30 to 120 seconds) leaves users waiting at frozen interfaces.
   - Enforce an explicit timeout bound of $\le 10.0\text{ s}$ on primary provider invocations to trigger failover before end-user abandonment.
2. **Decoupled Provider Bridge Dispatchers**:
   - Isolate vendor SDK specifics inside private adapter methods (`_call_openai`, `_call_anthropic`, `_call_gemini`).
   - Normalize API arguments (system prompts, user messages, max tokens, temperature) across client implementations.
3. **Execution Engine Skeleton**:

```python
import os
from openai import OpenAI, APIError as OpenAIAPIError
from anthropic import Anthropic, APIError as AnthropicAPIError

class ResilientModelEngine:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout = timeout_seconds
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "dummy"))

    def _call_openai(self, model: str, prompt: str) -> str:
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.timeout,
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, model: str, prompt: str) -> str:
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.timeout,
        )
        return response.content[0].text
```

> **Completion criterion**: Provider clients instantiated with unified $\le 10.0\text{ s}$ timeout guards and decoupled adapter bridges.

---

## 4. Automated Failover & Fallback Invocation

Execute primary model calls inside resilient exception-trapping blocks and trigger instant fallback upon transient degradation:

1. **Trap Provider-Specific Exceptions**:
   - Catch rate-limiting errors (`HTTP 429 Too Many Requests`), gateway timeouts (`HTTP 504`), service downtime (`HTTP 503`), socket timeouts, and provider SDK API errors.
2. **Log Structured Recovery Warning**:
   - Log explicit telemetry containing the failing provider, model name, exception message, and the designated fallback target.
   - Never silently swallow errors; silent failover masks upstream infrastructure degradations and creates unexpected billing shifts.
3. **Invoke Secondary Fallback Seamlessly**:
   - Instantly route the identical prompt payload to the secondary fallback model without breaking the calling application's execution chain.
   - Escalate to an unrecoverable `RuntimeError` only if both primary and secondary fallback calls fail.
4. **Resilient Failover Logic**:

```python
import structlog

logger = structlog.get_logger()

class ResilientModelEngine(ResilientModelEngine):
    def execute_provider_call(self, config: ModelConfig, prompt: str) -> str:
        if config.provider == "openai":
            return self._call_openai(config.model_name, prompt)
        elif config.provider == "anthropic":
            return self._call_anthropic(config.model_name, prompt)
        raise ValueError(f"Unsupported model provider: {config.provider}")

    def execute_with_fallback(
        self, primary: ModelConfig, fallback: ModelConfig, prompt: str
    ) -> tuple[str, str, bool]:
        # Attempt Primary Provider
        try:
            logger.info("calling_primary_provider", provider=primary.provider, model=primary.model_name)
            response = self.execute_provider_call(primary, prompt)
            return response, primary.model_name, False
        except (OpenAIAPIError, AnthropicAPIError, TimeoutError, Exception) as primary_error:
            logger.warning(
                "primary_model_failed_activating_fallback",
                primary_provider=primary.provider,
                primary_model=primary.model_name,
                fallback_provider=fallback.provider,
                fallback_model=fallback.model_name,
                error=str(primary_error),
            )

        # Attempt Secondary Fallback Provider
        try:
            logger.info("calling_fallback_provider", provider=fallback.provider, model=fallback.model_name)
            response = self.execute_provider_call(fallback, prompt)
            return response, fallback.model_name, True
        except Exception as fallback_error:
            logger.error("all_model_providers_failed", error=str(fallback_error))
            raise RuntimeError(
                f"Critical: Both primary ({primary.model_name}) and fallback ({fallback.model_name}) failed. "
                f"Root cause: {fallback_error}"
            ) from fallback_error
```

> **Completion criterion**: Primary failures caught within timeout bounds and execution smoothly recovered via secondary fallback with audit logging.

---

## 5. Output Schema Normalization & Telemetry Audit

Package all execution returns into a canonical, provider-agnostic data schema and emit telemetry for routing calibration:

1. **Normalize Output Schema**:
   - Prevent vendor-specific response objects (`openai.types.chat.ChatCompletion`, `anthropic.types.Message`) from leaking into application layers.
   - Standardize outputs into a typed response schema declaring execution status, resolved complexity tier, executed model, fallback flag, and clean text response.
2. **Emit Operational Observability & Cost Deltas**:
   - Record token counts, round-trip latency, model provider, and whether fallback occurred.
   - Track the volume ratio: verify that fast/budget models handle $\ge 60\%$ of total request traffic, validating that the complexity classifier's thresholds are properly tuned.
3. **Unified Orchestration Engine**:

```python
from pydantic import BaseModel

class NormalizedResponse(BaseModel):
    status: str
    complexity_tier: TaskComplexity
    model_used: str
    fallback_used: bool
    response: str

class SmartAIEngine:
    def __init__(self) -> None:
        self.analyzer = PromptAnalyzer()
        self.router = ModelRouter()
        self.executor = ResilientModelEngine(timeout_seconds=10.0)

    def process_request(self, user_prompt: str) -> NormalizedResponse:
        # Step 1: Deterministic offline analysis
        complexity = self.analyzer.analyze_complexity(user_prompt)

        # Step 2: Declarative routing resolution
        primary, fallback = self.router.get_models_for_tier(complexity)

        # Step 3 & 4: Resilient execution with fallback
        response_text, executed_model, fallback_used = self.executor.execute_with_fallback(
            primary=primary, fallback=fallback, prompt=user_prompt
        )

        # Step 5: Normalized schema packaging
        return NormalizedResponse(
            status="success",
            complexity_tier=complexity,
            model_used=executed_model,
            fallback_used=fallback_used,
            response=response_text,
        )
```

> **Completion criterion**: Downstream clients receive uniform `NormalizedResponse` schemas with verified telemetry logging and fallback tracking.

### The Visual Brief

Generate a standalone interactive HTML visual brief in `%TEMP%/dynamic-model-router-<timestamp>.html` summarizing routing metrics:
1. **Visual Telemetry**:
   - Render a dark-themed (`#0d1117`) dashboard loading Tailwind CSS and Mermaid.js via CDN.
   - Embed a **Routing Distribution Flowchart** illustrating query classification breakdown across simple, medium, and complex tiers.
   - Render a **Fallback Event Audit Table** detailing primary provider errors, failover frequencies, and latency deltas.
2. **Delivery**:
   - Deliver the clickable absolute file path to the operator for real-time routing inspection.

### Mandatory Checkpoint Gate

Enforce an operational review checkpoint (`RequestFeedback: true`) prior to committing routing table modifications or provider migrations:
1. **Provider Availability & Parity Audit**:
   - Verify that fallback models maintain functional parity with primary models before deployment.
   - Assert `primary.provider != fallback.provider` across all tiers to preserve infrastructure diversity.
2. **Operational Budget Sign-off**:
   - Validate that default timeouts ($\le 10.0\text{ s}$) and retry budgets are declared in `config.default.yaml`.

---

## Diagnostic Evaluation Scorecard Table

| Dimension | Evaluation Criterion | Target Threshold | Verification Mechanism | Passing Gate |
|---|---|---|---|---|
| **Classifier Latency** | Deterministic pre-routing classification speed | $\le 5.0\text{ ms}$ | Benchmark 1,000 synthetic prompts against regex & length scanner | P99 latency $< 5\text{ ms}$ with zero network calls |
| **Cost Distribution** | Ratio of routine traffic handled by low-cost models | $\ge 60\%$ of queries | Inspect routing decision logs across production traffic sample | $\ge 60\%$ routed to budget flash tier |
| **Failover SLA** | Timeout latency ceiling before initiating secondary failover | $\le 10.0\text{ s}$ | Simulate primary provider socket hang in automated mock harness | Secondary model invoked within $10.0\text{ s}$ |
| **Provider Diversity** | Primary and fallback reside on decoupled cloud infrastructures | $100\%$ decoupled | Audit routing matrix: assert `primary.provider != fallback.provider` | Zero shared infrastructure dependencies |
| **Schema Normalization**| Provider-specific SDK objects isolated from consumers | $100\%$ compliance | Typecheck downstream consumers against `NormalizedResponse` | Zero vendor SDK object leakage |

---

## Anti-Patterns

- **LLM-for-Routing** — Invoking an auxiliary language model to determine prompt complexity before routing; introduces 300–800ms of latency and doubles query token expenditure.
- **Lax Provider Timeout** — Relying on default SDK socket timeouts (30 to 120 seconds); freezes user interfaces and degrades end-user experience during upstream API degradations.
- **Vendor Monoculture Fallback** — Assigning primary and fallback models to the same cloud provider; causes concurrent double-failure during vendor-wide outages or authentication failures.
- **Silent Failover Drift** — Catching primary provider errors and executing fallbacks without logging warnings or failure telemetry; obscures chronic outages and causes unmonitored billing spikes.
- **Hardcoded Fallback-Free Invocation** — Invoking single proprietary models directly from business logic without fallback routing tables; creates fragile, single-point-of-failure applications.
