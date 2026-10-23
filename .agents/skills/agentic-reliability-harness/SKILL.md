---
name: agentic-reliability-harness
description: Build, verify, and govern agentic AI reliability testing harnesses across the Five Evaluation Levels, PEP gateway trust boundaries, loop detectors, chaos fault injection, and 3-state release gates. Do not use for generic web scraping, single-turn chatbots, or unauthenticated database administration.
---

# Agentic AI Reliability Testing Harness

`agentic-reliability-harness` is the authoritative testing, verification, and release gating engine for autonomous AI agents, derived from Vasuki Uday Kiran Vudathala's *Agentic AI Reliability: Build a Testing Harness for Tool Use, Guardrails, Loops, & Workflow Outcomes*.

Rather than falling victim to **"The Demo That Lied"**—where fluent conversational answers mask broken workflows, skipped validations, unauthorized tool mutations, or failed dependencies—this harness enforces the **Asymmetric Trust Boundary**. The System Under Evaluation (SUE) executes inside an instrumented sandbox accessing tools solely via a Policy Enforcement Point (PEP) Gateway, while the Control Plane directly reads authoritative world state to verify outcome correctness.

```
[1. Scenario & Boundary Isolation] ──► [2. Instrumented Execution & Faults] ──► [3. Five-Level Evaluation Engine]
                                                                                              │
                                                                                              ▼
[5. Three-State Confidence-Bounded Release Gate] ◄── [4. Behavioral Safety & Idempotence Audit] ◄────┘
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline budgets, loop thresholds, and gate policies.
Consult `scripts/arh_reliability_engine.py` for slotted domain models and evaluators.

---

## 1. Scenario & Boundary Isolation

Define strictly validated test scenarios and enforce physical separation between the agent and the evaluation control plane:

1. **Load Strict Scenario Fixtures**:
   - Ingest declarative scenario fixtures defining stimulus inputs, environment mocks, resource budgets, and expected business end states.
   - Reject scenarios missing explicit acceptance criteria, acceptable outcome sets, or state invariants at load time.
2. **Establish the Asymmetric Trust Boundary**:
   - Separate the **System Under Evaluation (SUE)** (model adapter, agent loop, tool selection, working memory) from the **Control Plane** (scenario runner, fault injector, trace collector, evaluators, release gate).
   - The SUE has zero access to scenario answer keys, golden trajectories, or direct storage backdoors.
3. **Bind Trusted Request Identity to PEP Gateway**:
   - Construct an immutable `SecurityContext` containing subject ID, actor ID, tenant ID, and granted authorization scopes.
   - Bind this identity to the `PolicyEnforcementGateway` at request initialization.
   - Prohibit the agent from constructing, forging, or expanding its own principal identity.
4. **Seed Authoritative World State**:
   - Populate initial database tables, account balances, and external system states directly from the control plane before agent invocation.

> **Completion criterion**: Scenario validated, SUE isolated behind the PEP Gateway, immutable identity bound, and initial world state seeded.

---

## 2. Gateway-Mediated Execution & Chaos Fault Injection

Execute the agent's ReAct step loop with strict watchdog bounds, policy authorization, and targeted fault injection:

1. **Enforce Watchdog Execution Budgets**:
   - Wrap the execution loop with hard watchdog limits: `max_steps`, `max_tool_calls`, and monotonic `wall_clock_ms`.
   - Terminate runaway executions immediately upon watchdog expiration, flagging the run as non-terminating.
2. **Mediate Tool Actions via Policy Enforcement Point (PEP)**:
   - Intercept every proposed tool invocation at the gateway before execution.
   - Validate argument schemas, enforce least-privilege scope checks, and require step approvals for high-consequence mutations.
   - Fail closed: any authorization failure, schema mismatch, or ambiguous policy returns an explicit rejection to the agent.
3. **Inject Systematic Chaos Faults**:
   - Inject transient faults across 4 failure domains: model availability, tool timeouts, state store corruption, and authorization service outages.
   - Test recovery pathways: verify whether the agent backs off gracefully, escalates, or aborts safely.
4. **Assemble Dual-Path Execution Records**:
   - Log runner events, gateway outcomes, security authorization decisions, and state store action journals independently.
   - Ensure telemetry loss in one component does not produce an evidence blackout for the evaluation suite.

> **Completion criterion**: ReAct loop executed to completion or bounded termination, all tool calls mediated by PEP, faults injected, and dual-path execution records assembled.

---

## 3. Five-Level Multi-Verdict Evaluation

Evaluate the execution record across the Five Structural Levels independently rather than collapsing evidence into a single score:

1. **Level 1 — Response Quality & Uncertainty Calibration**:
   - Verify final response text for factual consistency against observed tool outputs.
   - Assert proper uncertainty calibration: fail runs where the agent states certainty about failed, timed-out, or unperformed actions.
2. **Level 2 — Step Transitions & Loop/Non-Progress Detection**:
   - Evaluate transition validity between consecutive reasoning steps.
   - Execute the 3-vector loop detector:
     - *Action Repetition:* Flag identical tool calls repeated $\ge N$ times without state change.
     - *Ping-Pong Oscillation:* Flag alternating steps cycling between two tools without resolution.
     - *Semantic Stagnation:* Detect stagnant reasoning loops where observations produce zero state progress.
3. **Level 3 — Action & Tool Authorization Verification**:
   - Verify tool selection accuracy and argument validity against published schemas.
   - Assert all side-effecting actions occurred under valid scopes and necessary human approvals.
4. **Level 4 — Workflow Outcome Verification (Ground Truth)**:
   - Read the authoritative world state directly from the data store.
   - Compare actual database mutations against `acceptable_outcomes`.
   - Never accept the agent's narration or response text as evidence of outcome correctness.
5. **Level 5 — System Operational Envelope**:
   - Decompose latency by layer: model inference, gateway overhead, tool execution, and state commit.
   - Calculate retry amplification: ratio of physical tool attempts to logical operations.
   - Assert cost and token consumption remain within budgeted bounds.

> **Completion criterion**: Discrete verdicts generated for Response, Step, Action, Workflow, and System levels with supporting evidence.

---

## 4. Behavioral Safety & Idempotence Audit

Audit safety controls, write idempotence, and fault handling to guarantee zero silent corruption:

1. **Enforce the 4-Status Control Exercise Model**:
   - Classify all forbidden action attempts into one of four mutually exclusive statuses:
     - `pass`: Forbidden action was attempted and verifiably blocked by the authorization policy.
     - `fail_bypass`: Forbidden action executed or committed unauthorized state changes.
     - `not_exercised`: Model never attempted the forbidden action (control was untested; do not claim pass).
     - `indeterminate`: Ambiguous evidence or telemetry gap prevented definitive classification.
2. **Verify Write Idempotence**:
   - Test after-commit crash recovery: replay committed tool calls against the gateway.
   - Assert that duplicate action requests produce an effectively-once outcome with zero duplicate billing, records, or side-effects.
3. **Assert Zero False-Success Under Fault**:
   - For every scenario subjected to injected faults (timeouts, 500 errors, store rejections), assert the agent either recovered correctly or admitted failure.
   - **Hard Invariant:** The false-success-under-fault rate must be zero observed ($0\%$). Any run reporting success after an unhandled fault blocks release.

> **Completion criterion**: 4-status control exercise audit completed, write idempotence verified, and zero false success under fault proven.

---

## 5. Three-State Confidence-Bounded Release Gating

Transform granular run verdicts and aggregated rates into an authoritative, confidence-aware release decision:

1. **Enforce Three-State Gate Logic**:
   - Evaluate gate criteria into three distinct outcomes: `PASS`, `FAIL`, or `INCONCLUSIVE`.
   - `FAIL`: Measured failure or breach of a critical safety/quality threshold.
   - `INCONCLUSIVE`: Missing evidence, unexercised safety controls, or insufficient sample size.
   - CI builds exit non-zero on both `FAIL` and `INCONCLUSIVE`, preventing untested code from reaching production.
2. **Apply Statistical Confidence Intervals**:
   - Prohibit bare point estimates (e.g. "98% pass rate").
   - Compute Wilson score confidence intervals for Bernoulli success rates.
   - For critical zero-tolerance safety properties, apply the **Rule of Three** upper bound: $\text{Rate} \le 3 / N$ at 95% confidence.
3. **Execute Non-Inferiority Regression Testing**:
   - Compare candidate release metrics against versioned baseline snapshots.
   - Assert the lower bound of candidate performance does not regress beyond the defined non-inferiority margin $\Delta$.
4. **Publish Audit Scorecard Artifact**:
   - Generate a sanitized markdown/JSON scorecard capturing gate decisions, confidence intervals, sample sizes, and links to execution traces.

> **Completion criterion**: Three-state release decision rendered, confidence intervals computed, regression test passed, and scorecard published.

---

## Anti-Patterns

- **The Demo That Lied** — Assuming fluent conversational prose indicates underlying task success without verifying authoritative database records.
- **Answer-as-Evidence Fallacy** — Prompting the agent to self-report completion instead of reading physical state directly from the control plane.
- **Two-State Release Gate** — Forcing missing telemetry or unexercised controls into a binary pass/fail decision, masking coverage gaps.
- **Golden Path Overfitting** — Grading trajectories against a single brittle path, penalizing legitimate alternate routes that reach the correct outcome.
- **Agent-Supplied Identity** — Allowing the model to supply its own principal identity, tenant context, or authorization scopes.
- **Unexercised Guardrail Illusion** — Reporting a 100% safety pass rate when the model never actually attempted the forbidden action.
- **False Success Under Fault** — Silently continuing or claiming success when an external dependency or tool call fails or times out.
- **Bare Point Estimate Fallacy** — Shipping releases based on single point percentages without confidence intervals or minimum trial quotas.
