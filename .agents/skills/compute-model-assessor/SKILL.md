---
name: compute-model-assessor
description: Assess task complexity and recommend optimal model tiers and thinking budgets (High, Medium, Low, Off) calibrated for Gemini 3.7 Flash, Claude 3.7 Sonnet, and OpenAI o-series. Use when the user asks to assess compute, route models, estimate reasoning budget, or optimize LLM model tiering.
---

# Compute & Model Assessor Engine

`compute-model-assessor` is the authoritative task classification, dimensional scoring, and reasoning budget allocation engine for Brain Harness. Backed by `harness.services.compute_assessor`, it evaluates incoming user prompts, architectural tasks, and multi-agent subtasks across 5 orthogonal dimensions (Ambiguity, Span, Depth, Rigor, Concurrency)—recommending the optimal model tier and thinking budget (`High`, `Medium`, `Low`, `Off`) to maximize solution quality while eliminating latency and token waste.

Every compute assessment follows a strict five-stage progression:

```
[1. Task Surface Analysis] → [2. Compute Calibration] → [3. Visual Budget Brief] → [4. Recommendation Checkpoint] → [5. Routing Commit]
```

See [CARD.md](CARD.md) for the quick-reference summary card, calibration heuristics matrix, and invariants checklist.
Consult `/crafting-skills` for skill design standards and `/deepen-architecture` for architectural assessment.

---

## 1. Task Surface Analysis (5-Dimensional Complexity Vector)

Inspect the incoming user task across 5 core complexity dimensions using `DimensionalScorer`:

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

> **Completion criterion**: Task scored across the 5 dimensions, producing a `ComplexityVector` and an `AssessmentTrace`.

---

## 2. Compute Calibration & Multi-Provider Matrix

Map the assessed complexity level to explicit model tiers and provider-specific reasoning configurations:

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

> **Completion criterion**: Concrete model recommendation and thinking budget declared with provider-specific configuration arguments.

---

## 3. The Visual Budget Brief

Synthesize complexity evaluation, model tiers, and cost/latency tradeoffs into an interactive HTML visual brief using `ComputeVisualBriefGenerator`:

1. **Programmatic Generation**:
   ```python
   from harness.services.compute_assessor import ComputeRouter

   html_path = ComputeRouter.generate_visual_brief(
       "Refactor kernel service registry",
       files_count=4,
       is_architecture=True,
   )
   ```
2. **Target Location**: Writes to `%TEMP%\compute-assessor-<timestamp>.html` (Windows) or `/tmp/compute-assessor-<timestamp>.html` (Unix).
3. **Visual Standards**:
   - Dark mode (`#0d1117`) with Tailwind CSS and Mermaid.js.
   - 5-Dimensional Complexity Vector bars & Composite Score badge.
   - Interactive Mermaid Decision DAG.
   - High and Low complexity indicator lists.
4. **Delivery**: Surface the absolute file path with clickable links to the user.

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 4. Recommendation Checkpoint & CLI Integration

Present the compute recommendation and pause for user or harness confirmation:

### CLI Command
```bash
# Markdown block output
harness assess-compute "Refactor kernel service registry" --arch --files 4

# JSON output
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
```

> **Completion criterion**: Structured recommendation block emitted and approved.

---

## 5. Routing Commit & Provider Payload Synthesis

Commit the assessed configuration directly to the agent runtime using `ProviderReasoningAdapter`:

```python
from harness.services.compute_assessor import ComputeRouter, ProviderReasoningAdapter

assessment = ComputeRouter.assess("Refactor database schema", files_count=3, is_architecture=True)
payload = ComputeRouter.synthesize_payload(assessment)
# Returns:
# {
#   "model": "gemini-3.7-flash",
#   "temperature": 0.7,
#   "thinking_config": {"thinking_budget": 16384},
#   "thinking_budget": "high",
#   "reasoning_effort": "high"
# }
```

> **Completion criterion**: Target execution context configured with recommended model and thinking parameters.

---

## Anti-Patterns

- **Meta-Latency Waste** — Running an expensive high-reasoning model call just to decide if a simple task needs a high-reasoning model. Use rule-based heuristics or low-latency classification.
- **Context Blindness** — Underestimating the reasoning requirements of multi-file architectural refactors and selecting low-budget tiers.
- **Speculative Over-Reasoning** — Burning maximum thinking budget on mechanical formatting, boilerplate, or simple regex generation.
- **Lock-in Rigidity** — Hardcoding model names without providing cross-provider equivalents for Claude, OpenAI, and open-weights models.
- **Bypassing User Overrides** — Forcing automated routing without allowing explicit user override of model tier.
