# Pure Subagent Configuration Precedence Engine

## Context
In complex multi-agent architectures, subagent creation logic is often tangled with I/O, session state, transport mechanisms, and workspace directory creation. This makes testing, dry-running, remote spawning, and cross-framework reuse difficult and prone to state pollution.

## Distilled Learning
Separate the pure resolution phase of subagent creation into a standalone, zero-I/O module with deterministic precedence rules:
- **Strict Precedence Hierarchy**: Effective subagent configuration (model, persona, capability mode, isolation) resolves via:
  $$\text{Explicit Spawn Override} > \text{Role Definition} > \text{Persona Config} > \text{Parent Agent State}$$
- **Capability Mode Intersection**: When child agents specify tool permissions or depth limits, compute the intersection (`intersect_capability_modes`) against parent bounds, guaranteeing subagents can never escalate privileges beyond their parent context.
- **Resume Identity Validation**: When resuming previous subagent executions, validate resume identity (type and persona match checks) while ignoring benign runtime overrides.
- **Zero-I/O Seam**: Host adapters handle model catalog resolution and child filesystem directory creation, while the pure resolver computes system prompts, role files, and effective toolsets.

## Triggers & Seam Choices
- **Trigger**: Spawning hierarchical subagents, delegated specialist agents, or background swarm workers.
- **Seam Choice**: Implement as a pure resolution service (`harness.services.agent_resolution` or `xai-grok-subagent-resolution`) isolated from network transports and subprocess launchers.
