```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: agentic-reliability-harness                                   │
│ SKILL: agentic-reliability-harness                                   │
│ Category: verification / testing / harness-architecture              │
│ Version: 1.0.0                                                       │
│ Invocation: /agentic-reliability-harness                             │
│ Triggers: "agent reliability harness", "verify workflow outcome",    │
│           "tool-calling evaluation", "five-level evaluation",        │
│           "loop non-progress detect", "chaos fault injection",       │
│           "three-state release gate", "control plane vs sut"         │
│ Requires: "agent-harness-architect", "ai-native-harness-engineer",   │
│           "deterministic-validation-loop", "epistemic-memory-lifecycle"│
│ Target: Verification of Tool Use, Guardrails, Loops & Outcomes       │
└──────────────────────────────────────────────────────────────────────┘
```

# Agentic AI Reliability Testing Harness — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Scenario & Isolation** | Ingest strict scenario fixture & bind trusted identity to PEP gateway | Isolated SUE & Seeded World State | SUE isolated behind PEP; world state seeded |
| **Stage 2: Execution & Faults** | Run ReAct loop under watchdog; inject chaos faults; dual-path log | Dual-Path Execution Record | Bounded execution complete; all calls PEP-mediated |
| **Stage 3: 5-Level Evaluation** | Evaluate Response, Step, Action, Workflow & System levels independently | Five-Level Verdict Collection | All 5 structural levels assigned discrete verdicts |
| **Stage 4: Behavioral Audit** | Audit 4-status control exercise, write idempotence & fault resilience | Safety & Resilience Audit Dossier | Zero false-success under fault ($0\%$) observed |
| **Stage 5: 3-State Release Gate** | Render pass/fail/inconclusive decision with confidence intervals | Authoritative Scorecard Artifact | Gate decision rendered; intervals bounded; CI gated |

---

## The Three Foundational Pillars

### 1. The Asymmetric Trust Boundary
The agent (SUE) and the evaluation harness (Control Plane) must never share state backdoors or answer keys. The SUE reaches external systems only through a Policy Enforcement Point (PEP) Gateway with request-bound identity. The Control Plane inspects authoritative data stores directly.

### 2. The Five Independent Structural Levels
A single execution generates five independent verdicts:
- **Level 1 (Response):** Textual grounding and uncertainty calibration.
- **Level 2 (Step):** Transition validity and non-progress loop detection.
- **Level 3 (Action):** Tool schema adherence, argument correctness, and authorization.
- **Level 4 (Workflow):** Authoritative outcome correctness (ground truth).
- **Level 5 (System):** Latency breakdown, retry amplification, and operational cost.
Passing one level never excuses failure at another.

### 3. Three-State Confidence-Bounded Gating
Binary pass/fail gates conceal missing telemetry and untested controls. Release gates must support `PASS`, `FAIL`, and `INCONCLUSIVE`. Critical safety invariants enforce the **Rule of Three** ($p \le 3/N$) and require zero observed false successes under fault.

---

## Mandatory Invariants Checklist

- [ ] **Authoritative State as Sole Outcome Evidence**: The agent's final answer text is never accepted as evidence of workflow outcome correctness.
- [ ] **Request-Bound Trusted Identity**: Principal identities and scopes must be bound to the PEP Gateway at construction, never supplied by the model.
- [ ] **Four-Status Control Exercise**: Safety controls must distinguish `pass` (blocked), `fail_bypass` (breach), `not_exercised` (untested), and `indeterminate`.
- [ ] **Zero False-Success Under Fault**: Any execution that claims success or completes normally after an unhandled injected fault must strictly block release.
- [ ] **Three-State Gate Enforcement**: Missing, insufficient, or ambiguous evaluation telemetry must yield `INCONCLUSIVE` and exit non-zero in CI.
- [ ] **Slotted & Frozen Dataclass Domain**: All core domain records and verdicts must declare `slots=True, frozen=True` (Rule 12).
