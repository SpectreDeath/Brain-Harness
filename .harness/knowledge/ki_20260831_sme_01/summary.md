# MIMO 6D Dynamic Control Surface for Multi-Objective Agentic Harnesses

## Context
Agent harnesses often fail when forced into static configurations. Code generation tasks require low temperature, strict AST/JSON schema validation, and aggressive timeouts; conversely, long-horizon bug diagnosis requires expanded context windows, relaxed tool timeouts, and flexible trajectory branching.

## Distilled Learning
Implement a dynamic 6-Dimensional MIMO control surface (`MimoControlBridge`):
1. **D1 (Context Assembly)**: Dynamically bound pre-call RAG triplet limits (e.g. 5 for code generation vs 25 for deep forensic analysis).
2. **D2 (Tool Interaction)**: Configure per-task timeout and circuit breaker thresholds (e.g. 15.0s for deterministic tools vs 60.0s for long-running workflows).
3. **D3 (Generation Controls)**: Tune model decoding temperature (0.1 for deterministic code/syntax vs 0.3 for exploratory repair).
4. **D4 (Workflow Topology)**: Set dynamic routing mode policies (`auto`, `local_only`, `em_cubed_workflow`).
5. **D5 (Memory Management)**: Toggle session persistence across calls via SQLite WAL scratchpads.
6. **D6 (Output Processing)**: Enforce strict JSON Schema and AST surface validation before finalizing agent observations.

## Triggers & Seam Choices
- **Trigger**: When initializing agent step loops or dispatching multi-objective tasks in `StepExecutionEngine`.
- **Seam Choice**: Register `MimoControlBridge` as an IoC service (`service.sme.mimo_control`) to decorate workload execution payloads.
