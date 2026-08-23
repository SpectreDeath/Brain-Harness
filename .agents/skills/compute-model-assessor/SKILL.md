---
name: compute-model-assessor
description: Assess task complexity and recommend optimal model tiers and thinking budgets (High, Medium, Low, Off) calibrated for Gemini 3.7 Flash, Claude 3.7 Sonnet, and OpenAI o-series. Use when the user asks to assess compute, route models, estimate reasoning budget, or optimize LLM model tiering.
---

# Compute & Model Assessor Engine

`compute-model-assessor` is the authoritative task classification, dimensional scoring, token economics, reasoning budget allocation, and dynamic trajectory escalation engine for Brain Harness. Backed by `harness.services.compute_assessor`, it evaluates incoming user prompts, architectural tasks, and multi-agent subtasks across 5 orthogonal dimensions (Ambiguity, Span, Depth, Rigor, Concurrency)—recommending the optimal model tier and thinking budget (`High`, `Medium`, `Low`, `Off`) to maximize solution quality while eliminating latency and token waste.

Every compute assessment follows a strict five-stage progression:

```
[1. Task Surface Analysis] → [2. Compute Calibration & Economics] → [3. Visual Budget Brief] → [4. Recommendation Checkpoint] → [5. Routing Commit & Escalation]
```

See [CARD.md](CARD.md) for the quick-reference summary card, calibration heuristics matrix, and invariants checklist.
Consult `/crafting-skills` for skill design standards and `/deepen-architecture` for architectural assessment.

---

## 1. Task Surface Analysis & Scoring Profiles

Inspect the incoming user task across 5 core complexity dimensions using `DimensionalScorer` and configurable `ScoringProfile` presets:

1. **Solution Ambiguity & Branching (`ambiguity`)**:
   - Does the prompt require exploring multiple alternative designs or reconciling conflicting constraints?
   - *High (0.7–1.0)*: Novel architecture design, ambiguous bug diagnosis, race condition debugging.
   - *Medium (0.4–0.6)*: Implementing well-specified components, writing unit tests, refactoring with fixed contracts.
   - *Low (0.1–0.3)*: Mechanical syntax edits, regex drafting, boilerplate generation, formatting.

2. **Context Span & Codebase Depth (`span`)**:
   - How many files, interfaces, or dependency layers are impacted?
   - *Multi-module / DAG*: Requires cross-file reasoning and architectural invariant preservation.
   - *Single-seam*: Confined to one cohesive module or file.
   - *Zero-context*: Self-contained prompt with no workspace dependency.

3. **Algorithmic Depth & AST Manipulation (`depth`)**:
   - Does the task involve type checking, parser construction, topological sorting, or complex algorithms?

4. **Execution Rigor & Verification Cost (`rigor`)**:
   - What is the penalty for a hallucinated or flawed first attempt?
   - *Critical*: Structural migrations, kernel changes, persistent state mutations.
   - *Standard*: Routine feature additions with immediate automated test verification.
   - *Trivial*: Throwaway scratch scripts or informational answers.

5. **Concurrency & Race Potential (`concurrency`)**:
   - Does the task involve async event loops, thread safety, locks, semaphores, or distributed synchronization?

### Scoring Profile Presets:
- `balanced` (default): General balanced weights across all 5 dimensions.
- `reasoning_heavy`: Lower threshold for high reasoning, elevated weight on ambiguity and depth.
- `cost_optimized`: Higher threshold for high reasoning, minimizes token expenditure.
- `latency_optimized`: Biased towards faster turnaround tiers.

> **Completion criterion**: Task scored across the 5 dimensions, producing a `ComplexityVector` and an `AssessmentTrace`.

---

## 2. Compute Calibration, Economics & Multi-Provider Matrix

Map the assessed complexity level to explicit model tiers, token economics projections, and provider-specific reasoning configurations:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CALIBRATION HEURISTICS MATRIX                      │
├────────────┬─────────────────────┬───────────────────┬──────────────────┤
│ Complexity │ Gemini 3.7 Flash    │ Claude 3.7 Sonnet │ OpenAI o-series  │
├────────────┼─────────────────────┼───────────────────┼──────────────────┤
│ High       │ Thinking: `High`    │ Budget > 16k tok  │ o3-mini (high)   │
├────────────┼─────────────────────┼───────────────────┼──────────────────┤
│ Medium     │ Thinking: `Medium`  │ Budget ~4k–8k tok │ o3-mini (medium) │
├────────────┼─────────────────────┼───────────────────┼──────────────────┤
│ Low / Off  │ Thinking: `Low/Off` │ Standard / Off    │ gpt-4o-mini / Off│
└────────────┴─────────────────────┴───────────────────┴──────────────────┘
```

1. **High Complexity (Deep Reasoning Tier)**:
   - *Primary*: Gemini 3.7 Flash (`thinking_budget="high"`, 16,384 tokens), Claude 3.7 Sonnet (`budget_tokens=16000`), `o3-mini` (`effort="high"`).
   - *Alternative / Open*: DeepSeek-R1 (Full reasoning), Qwen-2.5-Coder-32B.
2. **Medium Complexity (Balanced Agentic Tier)**:
   - *Primary*: Gemini 3.7 Flash (`thinking_budget="medium"`, 4,096 tokens), GPT-4o, Claude 3.5 Sonnet.
   - *Alternative / Open*: DeepSeek-V3, Qwen-2.5-Coder-14B.
3. **Low / Mechanical Complexity (High-Throughput Tier)**:
   - *Primary*: Gemini 2.0 Flash / Flash-Lite (`thinking_budget="off"`, 0 tokens), GPT-4o-mini, Claude 3.5 Haiku.
   - *Alternative / Open*: Llama-3.3-8B-Instruct, Mistral-Small.

### Token Economics Projection (`ComputeEconomics`):
- `estimated_query_cost_usd`: Projected USD cost per query.
- `expected_latency_p50_seconds` / `expected_latency_p95_seconds`: Latency percentile distributions.

> **Completion criterion**: Concrete model recommendation, token economics, and thinking budget declared with provider-specific configuration arguments.

---

## 3. The Visual Budget Brief & Live Provider Studio

Synthesize complexity evaluation, model tiers, and cost/latency tradeoffs into an interactive HTML visual brief with live multi-provider payload copying using `ComputeVisualBriefGenerator`:

1. **Programmatic Generation**:
   ```python
   from harness.services.compute_assessor import ComputeRouter

   html_path = ComputeRouter.generate_visual_brief(
       "Refactor kernel service registry",
       files_count=4,
       is_architecture=True,
       profile="balanced",
   )
   ```
2. **Target Location**: Writes to `%TEMP%\compute-assessor-<timestamp>.html` (Windows) or `/tmp/compute-assessor-<timestamp>.html` (Unix).
3. **Visual Standards & Live Studio**:
   - Dark mode (`#0d1117`) with Tailwind CSS and Mermaid.js.
   - 5-Dimensional Complexity Vector bars, Composite Score badge, and Token Economics card.
   - Interactive Mermaid Decision DAG.
   - **Live Provider Payload Studio**: Interactive tabs to preview and copy exact JSON payloads for Google Gemini, Anthropic Claude, OpenAI o-series, DeepSeek, and Ollama.
4. **Delivery**: Surface the absolute file path with clickable links to the user.

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 4. Recommendation Checkpoint & CLI Integration

Present the compute recommendation and pause for user or harness confirmation:

### CLI Command
```bash
# Markdown block output with profile
harness assess-compute "Refactor kernel service registry" --arch --files 4 --profile balanced

# JSON output with economics
harness assess-compute "Fix typo in docstrings" --json

# Generate HTML visual brief
harness assess-compute "Migrate persistent database" --html
```

### Formal Structured Compute Recommendation Block:
```markdown
### [Compute Recommendation Block]
- **Complexity Assessment**: `High` (Tier: `high_reasoning`)
- **Primary Recommendation**: `gemini-3.7-flash` (Thinking Level: `HIGH`)
- **Reasoning Budget Tokens**: `~16,384 tokens`
- **Alternative / Peer Models**: `claude-3-7-sonnet | o3-mini | deepseek-r1`
- **Rationale**: High complexity: cross-module scope, structural ambiguity, or architectural constraints.
- **Vector Breakdown**: Ambiguity: 0.6, Span: 0.9, Depth: 0.8, Rigor: 0.7, Concurrency: 0.1
- **Economics Projection**: ~$0.0105 est. cost | Latency: p50 ~4.5s, p95 ~12.0s
```

> **Completion criterion**: Structured recommendation block emitted and approved.

---

## 5. Routing Commit, Dynamic Escalation & EventBus Telemetry

Commit the assessed configuration directly to the agent runtime, handle reactive retry escalation, and emit immutable audit events to the kernel `EventBus`:

### IoC Service & EventBus Audit:
```python
from harness.services.compute_assessor import (
    COMPUTE_ASSESSOR_SERVICE,
    ComputeAssessorService,
    DynamicTrajectoryEscalator,
    TrajectoryState,
)

# IoC Container resolution
assessor_service = ctx.require(COMPUTE_ASSESSOR_SERVICE)

# Asynchronous assessment with append-only EventBus telemetry
assessment = await assessor_service.assess_and_publish("Refactor database schema", files_count=3, is_architecture=True)
payload = assessor_service.synthesize_payload(assessment)
```

### Dynamic Trajectory Escalation on Error / Retry:
```python
# Track agent trajectory across attempts
trajectory = TrajectoryState()
trajectory.record_attempt(success=False, error="Syntax error during compilation")

# Automatically escalate thinking budget (e.g. Fast -> Standard -> High Reasoning)
escalated_assessment = assessor_service.escalate(assessment, trajectory)
print(f"Escalated model tier: {escalated_assessment.model_tier} (Budget: {escalated_assessment.budget_tokens:,} tokens)")
```

### Hierarchical Tree Budget Allocation:
```python
# Proportional token allocation across swarm tree branches
allocated_shares = DynamicTrajectoryEscalator.allocate_tree_budget(
    total_budget_tokens=32000,
    branch_weights=[0.5, 0.25, 0.25],
)
# Returns [16000, 8000, 8000]
```

> **Completion criterion**: Target execution context configured with recommended model, thinking parameters, and trajectory escalation policy.

---

## Anti-Patterns

- **Meta-Latency Waste** — Running an expensive high-reasoning model call just to decide if a simple task needs a high-reasoning model. Use rule-based heuristics or low-latency classification.
- **Context Blindness** — Underestimating the reasoning requirements of multi-file architectural refactors and selecting low-budget tiers.
- **Speculative Over-Reasoning** — Burning maximum thinking budget on mechanical formatting, boilerplate, or simple regex generation.
- **Lock-in Rigidity** — Hardcoding model names without providing cross-provider equivalents for Claude, OpenAI, and open-weights models.
- **Bypassing User Overrides** — Forcing automated routing without allowing explicit user override of model tier.
