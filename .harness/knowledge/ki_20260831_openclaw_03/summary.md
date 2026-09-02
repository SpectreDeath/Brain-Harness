# A2A (Agent-to-Agent) Multi-Agent Swarm Federation Protocol

## Context
As agent harnesses grow to handle complex domain engineering, running all specialized agents within a single process or memory space becomes brittle and resource-intensive. Sovereign agents deployed across different machines or containers need a standard contract to discover capabilities, dispatch sub-tasks, and track progress without shared state.

## Distilled Learning
The A2A v1.0 architecture implements:
1. **Agent Capability Advertisement**: Each agent registers supported tool sets, domain archetypes, and maximum context windows.
2. **Asynchronous Task Handover**:
   - Tasks are dispatched as structured envelopes containing task ID, input payload, context budget, and timeout.
   - The remote agent returns a pending acknowledgement, followed by asynchronous progress stream frames.
3. **Observation & Artifact Return**:
   - Upon task completion, the remote agent returns an observation envelope with status (`success`, `failure`, `requires_intervention`), result payload, and generated artifact references.
4. **Resilient Failure Recovery**: If the remote agent disconnects, the delegator receives a deterministic failover reason code and can either retry or fall back to a local sub-agent.

## Triggers & Seam Choices
- **Trigger**: Multi-agent task distribution, cross-host swarm execution, or external agent federation.
- **Seam Choice**: Encapsulate via `A2AFederationService` (`service.openclaw.a2a`) enabling Harness agents to delegate subtasks to external OpenClaw instances.
