# 4-Layer Isomorphic Transcript Data Engine with Granularity Subscriptions

## Architectural Summary
`@moonshot-ai/transcript` isolates event persistence from presentation using an isomorphic 4-layer model with dynamic granularity gating.

## Operational Guidelines
1. **4 Layers:**
   - **L1 Store:** Normalized, agent-indexed storage of execution frames.
   - **L2 Operations:** Idempotent operations (`appendDelta`, `closeBlock`, `commitTurn`) with cursor-based pagination.
   - **L3 Granularity Gate:** Filter streams based on client demand (`off`, `turn`, `block`, `delta`).
   - **L4 View Registry:** Headless, framework-agnostic rendering projection.
2. **Browser Safety:** Ensure the transcript module has zero runtime dependencies on Node.js or the agent runtime engine.
