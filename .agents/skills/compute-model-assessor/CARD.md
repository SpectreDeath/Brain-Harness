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
│ Version:     2.2.0 (Reactive IoC & Dynamic Escalation) │
│ Requires:    "crafting-skills"                         │
│ Provides:    "compute_budget_advice", "model_routing"  │
├────────────────────────────────────────────────────────┤
│ Target:      Assess task complexity (5D vector),       │
│              project token economics, dynamically     │
│              escalate reasoning on retries, and        │
│              synthesize multi-provider payloads.       │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Compute Assessment Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Task Analysis** | 5D vector: Ambiguity, Span, Depth, Rigor, Concurrency & Profiles | `ComplexityVector` & `AssessmentTrace` | Composite score & vector calculated |
| **2. Calibration & Economics** | Map complexity to model tiers + project USD cost & latency | Model tier matrix, tokens, & `ComputeEconomics` | Economics & provider args resolved |
| **3. Visual Brief** | Render interactive HTML radar brief + Live Provider Studio in `%TEMP%` | `%TEMP%\compute-assessor-*.html` | Dark-mode HTML brief & JSON studio delivered |
| **4. Checkpoint** | Present structured compute recommendation block / CLI | `implementation_plan.md` / CLI output | Structured recommendation approved |
| **5. Routing & Escalation** | Synthesize vendor payloads, emit `EventBus` audit log, & escalate retries | `ProviderReasoningAdapter` / `DynamicTrajectoryEscalator` | Execution payload injected with retry escalation |

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
# CLI usage with profiles and economics
harness assess-compute "Refactor kernel service registry" --arch --files 4 --profile balanced
harness assess-compute "Fix docstrings" --json
harness assess-compute "Migrate schema" --html
```

```python
# Programmatic usage (Static or IoC with Escalation)
from harness.services.compute_assessor import (
    ComputeRouter,
    COMPUTE_ASSESSOR_SERVICE,
    ComputeAssessorService,
    DynamicTrajectoryEscalator,
    TrajectoryState,
)

# Static direct access
assessment = ComputeRouter.assess("Refactor database schema", files_count=3, is_architecture=True)
payload = ComputeRouter.synthesize_payload(assessment)
html_path = ComputeRouter.generate_visual_brief("Refactor database schema", files_count=3, is_architecture=True)

# IoC Container access with EventBus telemetry
assessor = ctx.require(COMPUTE_ASSESSOR_SERVICE)
assessment = await assessor.assess_and_publish("Refactor database schema", is_architecture=True)

# Reactive trajectory escalation on retry/failure
trajectory = TrajectoryState()
trajectory.record_attempt(success=False, error="Syntax error")
escalated = assessor.escalate(assessment, trajectory)
```

---

## Anti-Patterns Cheat Sheet

- **Meta-Latency Waste**: Running expensive high-reasoning models just to classify a prompt.
- **Context Blindness**: Underestimating multi-file refactoring and picking low-budget models.
- **Speculative Over-Reasoning**: Burning max thinking budget on simple mechanical translations.
- **Lock-in Rigidity**: Failing to provide cross-provider fallbacks (Claude, OpenAI, Ollama, open weights).
- **Bypassing Overrides**: Forcing automated decisions without allowing user overrides.

---

## Invariants & Guardrails

- [ ] **Low-Latency Classifier**: Never execute heavy reasoning loops for the classification step.
- [ ] **Cross-Provider Mapping**: Always provide equivalent recommendations for Gemini, Claude, and OpenAI.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML brief with Live Provider Studio before executing large runs.
- [ ] **Recommendation Block Present**: Always emit the formal structured `[Compute Recommendation Block]`.
- [ ] **Preserve User Overrides**: User-specified model and thinking settings must always take precedence.
- [ ] **Trajectory Escalation Ready**: Multi-attempt loops must escalate reasoning budget when encountering task errors.
