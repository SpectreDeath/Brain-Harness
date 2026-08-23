# Skill Summary Card: `compute-model-assessor`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        compute-model-assessor                    │
│ Category:    routing / compute-optimization            │
│ Invocation:  /assess-compute / harness assess-compute  │
│ Trigger:     "assess compute", "route model",          │
│              "recommend model", "thinking budget",     │
│              "estimate reasoning level", "model tier"  │
│ Version:     2.0.0 (Deepened Seam)                     │
│ Requires:    "crafting-skills"                         │
│ Provides:    "compute_budget_advice", "model_routing"  │
├────────────────────────────────────────────────────────┤
│ Target:      Assess task complexity (5D vector) and    │
│              synthesize provider reasoning payloads.   │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Compute Assessment Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Task Analysis** | 5D vector: Ambiguity, Span, Depth, Rigor, Concurrency | `ComplexityVector` & `AssessmentTrace` | Composite score & vector calculated |
| **2. Calibration** | Map complexity to Gemini, Claude & OpenAI model tiers | Model tier matrix & token budget | Provider-specific args resolved |
| **3. Visual Brief** | Render interactive HTML radar brief in `%TEMP%` | `%TEMP%\compute-assessor-*.html` | Dark-mode HTML brief delivered |
| **4. Checkpoint** | Present structured compute recommendation block / CLI | `implementation_plan.md` / CLI output | Structured recommendation approved |
| **5. Routing Commit** | Synthesize vendor payload parameters (Gemini, Claude, OpenAI) | `ProviderReasoningAdapter.get_provider_payload()` | Execution payload injected into LLM call |

---

## Calibration Matrix: Gemini 3.7 & Industry Peers

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

---

## CLI & Programmatic Seams

```bash
# CLI usage
harness assess-compute "Refactor kernel service registry" --arch --files 4
harness assess-compute "Fix docstrings" --json
harness assess-compute "Migrate schema" --html
```

```python
# Programmatic usage
from harness.services.compute_assessor import ComputeRouter

assessment = ComputeRouter.assess("Refactor database schema", files_count=3, is_architecture=True)
payload = ComputeRouter.synthesize_payload(assessment)
html_path = ComputeRouter.generate_visual_brief("Refactor database schema", files_count=3, is_architecture=True)
```

---

## Anti-Patterns Cheat Sheet

- **Meta-Latency Waste**: Running expensive high-reasoning models just to classify a prompt.
- **Context Blindness**: Underestimating multi-file refactoring and picking low-budget models.
- **Speculative Over-Reasoning**: Burning max thinking budget on simple mechanical translations.
- **Lock-in Rigidity**: Failing to provide cross-provider fallbacks (Claude, OpenAI, open weights).
- **Bypassing Overrides**: Forcing automated decisions without allowing user overrides.

---

## Invariants & Guardrails

- [ ] **Low-Latency Classifier**: Never execute heavy reasoning loops for the classification step.
- [ ] **Cross-Provider Mapping**: Always provide equivalent recommendations for Gemini, Claude, and OpenAI.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML brief before executing large multi-tier runs.
- [ ] **Recommendation Block Present**: Always emit the formal structured `[Compute Recommendation Block]`.
- [ ] **Preserve User Overrides**: User-specified model and thinking settings must always take precedence.
