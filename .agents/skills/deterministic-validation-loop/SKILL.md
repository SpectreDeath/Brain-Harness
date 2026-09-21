---
name: deterministic-validation-loop
description: Architect, implement, and operate spec-first deterministic validation loops (3-tier validation, exact error injection, and bounded retries) for LLM structured outputs. Do not use for subjective or open-ended prose evaluation where deterministic truth functions cannot be written.
---

# Deterministic Validation Loop: Spec-First Agent Output Reliability

The `deterministic-validation-loop` skill provides the definitive engineering methodology for ensuring absolute correctness when AI agents generate structured outputs (JSON schemas, deployment configurations, SQL queries, ASTs, and API payloads).

While popular tutorials propose LLM "reflection" turns to review structured outputs, reflection produces **blind spot symmetry**—where the reviewing model rubber-stamps invalid outputs as *"looks good!"*, leaking broken state into production. This skill synthesizes Manish Ramavat's foundational literature (*What to Do When Reflection Won't Fix Your AI Agent's Output*, freeCodeCamp, 2026), enforcing a strict **spec-first architecture**, 3-tier deterministic validation hierarchy, exact machine-generated error injection, and bounded give-up triage.

```
[1. Spec & Validator Definition] -> [2. Graph & Node Topology] -> [3. Error Feedback Injection] -> [4. Bounded Budget & Triage] -> [5. The Visual Brief & Mandatory Checkpoint Gate]
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and verification checklist.
Consult [self-evaluating-ai-pipeline](../self-evaluating-ai-pipeline/SKILL.md) for subjective/open-ended evaluation and [crafting-skills](../crafting-skills/SKILL.md) for skill authoring standards.

---

## 1. Spec & Validator Definition (Spec-First Architecture)

Build the validator **before** writing agent prompts. The validator *is* your machine-checkable specification. It defines "correct" in unambiguous, executable terms.

1. **Implement the 3-Tier Validation Hierarchy**:
   - **Tier 1 (Structural Syntax & Schema)**: Verify JSON parseability, presence of required attributes, and basic primitive types using `jsonschema.validate()` or native parsers. Bail early on failure; never check business rules against unparsed or broken data structures.
   - **Tier 2 (Boundary & Pattern Constraints)**: Verify numerical intervals (e.g. `1 <= replicas <= 20`), memory/CPU limits, and regex format conformity (e.g. `^[a-z][a-z0-9-]*$`).
   - **Tier 3 (Cross-Field Business Logic Invariants)**: Verify multi-attribute relational invariants (e.g., `replicas > 5` requires `cpu_limit >= 1.0`; `timeout_seconds < interval_seconds`). These are domain-specific invariants absent from model training priors.
2. **Standardize Validator Contract**:
   - Expose an unambiguous signature:
     ```python
     def validate_payload(payload: dict) -> tuple[bool, list[str]]:
         """Returns (is_valid, list_of_error_strings)."""
     ```
   - Ensure errors are returned as human-readable, actionable strings targeting specific keys.

> **Completion criterion**: Validator function authored, decoupled from LLM dependencies, executing all 3 tiers in <1ms, returning `(is_valid, errors)`.

---

## 2. Stateful Graph & Node Topology Synthesis

Wire the generator and validator into a cyclic state graph (e.g., using LangGraph or an in-process ReAct state engine).

1. **Declare State Schema**:
   ```python
   from typing import TypedDict

   class ValidationState(TypedDict):
       request: str
       payload: dict | None
       errors: list[str]
       attempts: int
   ```
2. **Construct Discrete Nodes**:
   - `generate_node(state)`: Calls the LLM to synthesize the payload. When `state["errors"]` is populated, injects previous errors directly into the prompt. Increments `attempts`.
   - `validate_node(state)`: Runs the pure deterministic validator. Bails if payload is `None` (JSON parse error) and updates `state["errors"]`.
3. **Establish Deterministic Routing Edge**:
   - `route_condition(state) -> "done" | "retry"`:
     - Returns `"done"` if `len(state["errors"]) == 0`.
     - Returns `"retry"` if `state["attempts"] < 3`.
     - Returns `"done"` if `state["attempts"] >= 3` (escalating to failure triage).

> **Completion criterion**: State machine graph compiled with explicit generate, validate, and conditional retry edges terminating deterministically.

---

## 3. Unambiguous Error Feedback Injection

Differentiate between **error detection** (delegated to the deterministic validator) and **error correction** (delegated to the LLM).

1. **Zero Natural Language Critique**:
   - Never use vague conversational critique (*"Please make sure the CPU limits are appropriate"*).
   - Never ask an LLM to evaluate whether its own output meets the spec.
2. **Structured Delta Injection**:
   - When retrying, inject the exact list of machine-generated error messages directly into the user/human turn:
     ```python
     content = f"Generate configuration for: {state['request']}"
     if state["errors"]:
         content += "\n\nYour previous attempt had these errors:\n"
         content += "\n".join(f"- {err}" for err in state["errors"])
         content += "\nFix ALL of them."
     ```
3. **Clean Prompt Hygiene**:
   - Maintain the static system prompt as a concise definition of the required fields. Do not bloat prompts with historical conversation banter.

> **Completion criterion**: Generation node dynamically appends exact bulleted validator error strings on all retry iterations.

---

## 4. Bounded Budget & Give-Up Triage

Enforce a hard ceiling on retries. An agent that fails three consecutive attempts is suffering from prompt/spec ambiguity, not random generation noise.

1. **Cap Retries at Exactly 3 Attempts**:
   - Prohibit unbounded retry loops ($>3$ attempts). Attempting 4+ times burns API tokens with near-zero marginal recovery.
2. **Execute Three-Way Triage on Failure**:
   - **Telemetry Logging**: Record the original request, raw invalid payload, and final error list to a dedicated observability sink. This forms the primary dataset for refining ambiguous prompts or conflicting schemas.
   - **Typed Rejection (Fail Closed)**: Reject the request with an explicit error response (e.g., HTTP 422 Unprocessable Entity with error list). Never allow unvalidated or fallback-default payloads to silently leak downstream.
   - **Human Escalation**: For critical operational paths (deployment pipelines, database migrations), route the failed state to a human supervisor queue.

> **Completion criterion**: Graph halts at `attempts == 3` with structured error logging and typed rejection, preventing silent corruptions.

---

## 5. Applicability & Verification Gate

Audit the agent application to ensure the pattern is correctly applied and verified with automated test contracts.

1. **The Boolean Truth Test**:
   - Ask: *Can you write a function returning `true` or `false` for this agent output?*
   - If yes &rarr; Enforce `deterministic-validation-loop`.
   - If no &rarr; Route to semantic LLM evaluation (`self-evaluating-ai-pipeline`) or human review.
2. **Test Contract Verification**:
   - Author characterization tests verifying:
     - Valid payload passes on attempt 1.
     - Invalid syntax/schema triggers immediate Tier 1 rejection.
     - Boundary and cross-field errors trigger retry with injected errors and pass on attempt 2.
     - Persistent errors halt cleanly at attempt 3 with logged triage.

> **Completion criterion**: Test suite asserts passing payloads, recovery on retry, and clean failure closure at attempt 3 with zero unhandled exceptions.

---

## 6. Micro-Kernel IoC & CLI Seams

The deterministic validation loop is elevated into the Brain Harness micro-kernel as an authoritative service and CLI:

1. **Domain Engine**: [validation_loop_engine.py](scripts/validation_loop_engine.py) provides slotted, frozen models (`ValidationSpec`, `ValidationRule`, `DeterministicValidationEngine`) with sub-millisecond execution and built-in preset specs (`deployment_config`, `plugin_manifest`).
2. **IoC Service Key**: [`DETERMINISTIC_VALIDATION_SERVICE_KEY`](../../src/harness/services/deterministic_validation.py) exports `ServiceKey[DeterministicValidationService]` for in-memory resolution (`context.require()`).
3. **Plugin Packaging**: [deterministic_validation_loop plugin](../../plugins/agent_orchestration/deterministic_validation_loop/README.md) registers the service and exposes agent tools (`validate_payload`, `run_validation_loop`).
4. **Headless Click CLI**: Execute validation from terminal or CI scripts:
   - `harness validation-loop specs`
   - `harness validation-loop validate --spec deployment_config --file config.json`
   - `harness validation-loop run --request "Deploy service" --spec deployment_config`
   - `harness validation-loop brief --output brief.html`

---

## Anti-Patterns

- **Blind Spot Symmetry** — Asking an LLM to critique another LLM's structured output. The identical weights and priors that missed the constraint during generation will approve the broken output during review.
- **Invisible False Positives** — Relying on reflection steps that say *"looks good!"* on broken JSON, allowing corrupt configurations to silently reach production.
- **Infinite Token Burning** — Allowing loops to retry 5-10 times hoping for luck, rather than halting at 3 attempts and escalating spec ambiguity.
- **Spec-Last Inversion** — Writing agent system prompts before writing the validator function. The validator *is* the specification.
- **Silent Leakage** — Falling through to downstream execution on exhausted retries without raising an error or marking state as invalid.
- **Vague Critique Injection** — Feeding conversational feedback (*"please check your numbers"*) instead of exact machine-generated error strings.
