## Authoritative Critic Seam Consolidation & Adapter Pattern

### Problem
In multi-agent systems and plugin architectures, quality gates, safety checks, and evaluation logic often fragment across multiple shallow modules (e.g. `critic_loop`, `evaluator_critic`, `agent_debater`). This causes:
1. **Duck-typed string dispatch**: Tools invoking string names rather than typed interfaces.
2. **Duplicated heuristics**: Redundant regex or AST safety scanners across multiple plugins.
3. **Broken IoC Lifecycles**: Some modules implement plain procedural functions without registering service keys into the IoC container.

### Solution Pattern: Consolidated Deep Seam with Thin Delegation Adapters
Instead of maintaining fragmented evaluation entrypoints or breaking downstream callers with abrupt renames:
1. **Consolidate Core Logic**: Elevate the primary module (`critic_loop`) into an authoritative, typed `@runtime_checkable` `CriticEvaluationService` Protocol with a registered `ServiceKey[CriticEvaluationService]`.
2. **Preserve Compatibility via Aliases**: Export legacy keys as aliases (`CRITIC_LOOP_KEY = CRITIC_EVALUATION_SERVICE_KEY`).
3. **Provide Thin Delegation Adapters**: Retain legacy plugin packages (`evaluator_critic`, `agent_debater`) as lightweight adapters that subclass `HarnessPlugin`, implement standard `on_load(context)`, and delegate calls to the centralized service instance.
4. **Zero-Fork Baseline Budgets**: Co-locate a `config.default.yaml` establishing baseline thresholds (rubric cutoffs, max refinement iterations, code LOC limits).

### Architectural Rules Enforced
- **Rule 2**: Typed `ServiceKey[T]` registration and resolution.
- **Rule 18**: Domain-partitioned plugins with cohesive boundaries.
- **Rule 20**: In-place deepening over shallow tool sprawl.
- **Rule 44**: Zero-fork configuration baseline budgets.
