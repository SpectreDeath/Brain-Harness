# Dynamic Model Router Plugin

An in-process sandboxed plugin providing **3-tier dynamic model switching & resilient failover** for AI coding agents.

## Provenance
Synthesized from Chidiebere Njoku's literature (*How to Build AI Applications That Switch Models Automatically*, freeCodeCamp, 2026) and grounded in Knowledge Vault item `ki_njoku_dynamic_model_routing`.

## Architecture & Capabilities

1. **Deterministic Offline Profiling**: Regex & token heuristics classify complexity (`SIMPLE`, `MEDIUM`, `COMPLEX`) in $< 5\text{ ms}$ with zero network overhead.
2. **Declarative Routing Table with Provider Diversity**: Asserts `primary.provider != fallback.provider` across all tiers to prevent vendor outage lockups.
3. **Strict Timeout Encasement**: Socket timeouts constrained to $\le 10.0\text{ s}$.
4. **Resilient Failover Chaining**: Primary degradation triggers secondary fallback with structured recovery telemetry.
5. **Canonical Normalization**: Standardizes outputs into `NormalizedResponse` schemas.

## Provided Services
- `service.dynamic_model_router` (`DYNAMIC_MODEL_ROUTER_SERVICE_KEY`)

## CLI Seams
- `harness router profile "<prompt>"`
- `harness router route [--complexity simple|medium|complex]`
- `harness router simulate "<prompt>" [--fail-primary]`
- `harness router brief`


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `profile_prompt` | `(prompt)` | Deterministic syntax and keyword complexity profiling (<5ms, zero-LLM) |
| `resolve_routing` | `(complexity, cost_ceiling)` | Resolve primary and fallback model configuration asserting provider diversity |
| `route_and_execute` | `(prompt, override_complexity)` | Execute prompt with automated fallback rollover and circuit breaker protection |
| `model_router_visual_brief` | `(output_path)` | Generate interactive HTML visual brief with telemetry and routing distribution |
