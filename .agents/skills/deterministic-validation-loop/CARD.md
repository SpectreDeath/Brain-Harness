┌─────────────────────────────────────────────────────────────┐
│ SKILL: deterministic-validation-loop                        │
├─────────────────────────────────────────────────────────────┤
│ DESCRIPTION: Spec-first deterministic validation loops with │
│ 3-tier validation, exact error injection, & bounded retries │
└─────────────────────────────────────────────────────────────┘

## Stage Progression Matrix

| Stage | Focus Area | Core Mechanism | Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Spec & Validator** | Spec-First Code | 3-Tier Hierarchy: Schema, Bounds, Cross-Field | <1ms latency, pure code, returns `(bool, list[str])` |
| **2. Graph Topology** | State Machine | LangGraph / ReAct cyclic graph | Explicit generate, validate, and route edges |
| **3. Error Injection** | Delta Feedback | Inject exact bulleted error strings | Unambiguous `- {err}` injected into human turn |
| **4. Bounded Budget** | Give-Up Triage | Hard ceiling at <= 3 attempts | Halt at 3, log telemetry, return HTTP 422 |
| **5. Brief & Gate** | Visual Brief & Gate | Interactive HTML brief, boolean gate | Interactive brief in %TEMP%, 0 errors pass gate |

---

## Three Pillars Cheat Sheet

### Pillar 1: 3-Tier Deterministic Validation
- **Tier 1 (Structural)**: JSON parseability, required fields, primitive types via `jsonschema`. Bail early on failure.
- **Tier 2 (Boundary)**: Numerical ranges (`1 <= replicas <= 20`), format regex (`^[a-z][a-z0-9-]*$`), resource minimums.
- **Tier 3 (Cross-Field)**: Multi-attribute relational invariants (`replicas > 5` requires `cpu_limit >= 1.0`).

### Pillar 2: Bifurcated Division of Labor
- **Error Detection**: Outsource 100% to deterministic code (0 API tokens, 0 hallucinations, microseconds).
- **Error Correction**: Delegate 100% to LLM by feeding exact machine-generated error strings.
- **The Invariant**: *"LLMs are excellent at fixing errors when told exactly what is wrong; they are terrible at finding their own errors."*

### Pillar 3: Bounded Budget & Failure Triage
- **Attempt Ceiling**: Hard cap of 3 attempts. Attempt 4+ has diminishing returns and signals spec/prompt ambiguity.
- **Telemetry**: Log original prompt + final validation error list to diagnose schema/prompt design flaws.
- **Fail Closed**: Return explicit typed error (HTTP 422); never allow unvalidated state to leak into production.

---

## Verification Checklist

- [ ] Frontmatter description bounded between 100 and 350 characters with action verbs and negative boundary.
- [ ] Validator function implemented in pure deterministic code, completely independent of LLM context.
- [ ] Validator covers all 3 tiers: Schema (Tier 1), Bounds/Regex (Tier 2), and Cross-Field Logic (Tier 3).
- [ ] Validator bails early on Tier 1 structural syntax failures before checking cross-field invariants.
- [ ] State graph implements deterministic conditional routing terminating on 0 errors or attempt 3.
- [ ] Retry prompt appends exact bulleted list of validator errors with *"Fix ALL of them"* directive.
- [ ] Bounded budget halts execution at 3 attempts and triggers structured ambiguity logging.
- [ ] System fails closed with typed rejection (HTTP 422) rather than leaking unvalidated state.
- [ ] Companion `CARD.md` utilizes single-pipe borders (`│`) and exact `SKILL:` header.
