# Knowledge Item: Agentic AI Reliability Testing Harness

## Epistemic Distillation

### 1. Ground-Truth Mental Models

#### The "Demo That Lied" & The Asymmetric Trust Boundary
A demonstration of an autonomous AI agent produces a polite, well-structured, persuasive response claiming that a user's task was completed. Yet under the surface, the agent may have skipped a mandatory validation check, attempted an unauthorized action, double-billed an account, or ignored a downstream 500 error.
- **The Core Axiom**: The agent's final words are never entered as evidence of outcome correctness.
- **The Asymmetric Trust Boundary**: The system under evaluation (SUE) and the evaluation control plane must be physically and logically separated. The SUE interacts with external resources *only* through a Policy Enforcement Point (PEP) Gateway. The control plane inspects authoritative world state directly and cannot be swayed by model narrative.

#### The Two Orthogonal Taxonomies
Evaluating agentic systems requires disentangling two frequently confused dimensions:
1. **The Six Evaluation Activities (When and Why evidence is gathered)**:
   - *Model Evaluation:* Offline benchmark metrics on base models.
   - *Response Evaluation:* Measuring output relevance, toxicity, and groundedness.
   - *Agent Evaluation:* Offline verification of multi-step plans and tool call traces.
   - *Workflow Verification:* Verifying authoritative state changes for business outcomes.
   - *System Reliability Testing:* Stress testing, load, concurrency, and fault injection.
   - *Production Monitoring:* Real-time telemetry, drift detection, and canary verification.
2. **The Five Evaluation Levels (What structural object is evaluated)**:
   - *Level 1 (Response):* Is the text factual, relevant, grounded, and appropriately calibrated?
   - *Level 2 (Step):* Are intermediate transitions valid and free from non-progress loops?
   - *Level 3 (Action):* Was the correct tool invoked with valid arguments and authorized scopes?
   - *Level 4 (Workflow):* Did the world reach the intended business end state?
   - *Level 5 (System):* Did execution remain within latency, cost, retry, and fault budgets?

A single execution receives five independent verdicts. Passing one level never compensates for failure at another.

#### The 4-Status Control Exercise Model
When evaluating security, guardrails, or safety policies, binary pass/fail is actively misleading:
- **`pass`**: The agent attempted a prohibited action, and the policy enforcement control successfully intercepted and blocked it.
- **`fail_bypass`**: The agent attempted a prohibited action, and the control failed to block it, resulting in unauthorized execution.
- **`not_exercised`**: The agent never attempted the prohibited action during the scenario. The control remains unverified. Claiming a "pass" here is an illusion of safety.
- **`indeterminate`**: Telemetry dropped out or evidence is ambiguous.

#### Invariant: Zero False-Success Under Fault
When chaos faults (timeouts, rate limits, network disconnects, storage rejections) are injected into agent execution:
- The agent must either recover via an authorized fallback path or faithfully halt and report failure.
- If an agent encounters an unhandled fault and subsequently claims successful task completion, the run violates the **Zero False-Success Under Fault** invariant ($0\%$). Any observed false success strictly blocks a production release.

#### Three-State Release Gates & Statistical Bounds
Binary release gates force missing evidence into false passes or false regressions.
- **Three Decisions**:
  - `PASS`: All required scenarios executed, all critical metrics passed, and confidence intervals meet thresholds.
  - `FAIL`: Measured regression or breach of a critical safety bound.
  - `INCONCLUSIVE`: Missing telemetry, insufficient trials, or unexercised safety controls. In CI, both `FAIL` and `INCONCLUSIVE` exit non-zero.
- **Statistical Confidence**:
  - Point estimates are prohibited. Success rates require Wilson score lower bounds.
  - Zero-tolerance safety targets require the **Rule of Three** upper bound: $p \le 3 / N$ at 95% confidence.

---

## 2. Decision Heuristics for Engineers & Architects

1. **Before modifying agent prompts or tools:** Run an offline baseline scenario suite capturing both tool trajectories and database state deltas.
2. **When authoring scenarios:** Never write an expectation that evaluates the agent's prose for business logic. Declare `acceptable_outcomes` and `expected_state_invariants` against the database schema.
3. **When binding identity:** Always bind an immutable `SecurityContext` to the PEP Gateway at request initialization. If a model attempts to pass an `identity` or `tenant_id` parameter, reject the call.
4. **When configuring CI gates:** Set `on_missing_evidence: "block"` to prevent telemetry outages from silently turning into green releases.

---

## 3. Mandatory Anti-Pattern Defenses

- **The Demo That Lied:** Never trust a convincing conversational summary as proof of task success. Always read the authoritative database record.
- **Answer-as-Evidence Fallacy:** Never prompt an agent to verify whether it completed a task. Inspect the world state externally.
- **Golden Path Trajectory Overfitting:** Never require tool calls to match a single brittle sequence; verify preceding reads, argument validity, and state outcomes.
- **Unexercised Guardrail Illusion:** Never count scenarios where the model was benign as proof that guardrails work. Explicitly report `not_exercised`.
