# Deterministic Validation Loop Plugin

The `plugin.deterministic_validation_loop` plugin packages the spec-first 3-tier deterministic validation loop (Manish Ramavat 2026: *What to Do When Reflection Won't Fix Your AI Agent's Output*) into a first-class micro-kernel IoC service.

## Core Capabilities

- **3-Tier Validation Hierarchy**:
  - **Tier 1 (Structural Syntax & Schema)**: JSON parseability, required properties, primitive types via `jsonschema`. Bails early on failure.
  - **Tier 2 (Boundary & Pattern Constraints)**: Numerical ranges, regex formats, and resource bounds.
  - **Tier 3 (Cross-Field Invariants)**: Relational multi-attribute business logic invariants.
- **Bifurcated Division of Labor**:
  - **Error Detection**: 100% deterministic code (<1ms execution, 0 tokens, 0 hallucinations).
  - **Error Correction**: 100% delegated to LLM via exact machine-generated error delta injection.
- **Bounded Budget & Triage**:
  - Hard cap at 3 attempts.
  - Fails closed with typed HTTP 422 rejection and audit telemetry.

## Provided Services

- `service.deterministic_validation` &rarr; `DETERMINISTIC_VALIDATION_SERVICE_KEY` implementing `DeterministicValidationService`.

## Tools Exposed

- `validate_payload(payload, spec)`: Validate JSON payload against a preset or schema.
- `run_validation_loop(request, spec, max_attempts)`: Run state machine loop.
- `get_preset_spec(name)`: Retrieve built-in preset specification.
- `validation_visual_brief(output_path)`: Render interactive HTML review brief.
