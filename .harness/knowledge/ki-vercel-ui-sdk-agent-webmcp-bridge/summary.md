# Vercel UI SDK: Agent Bridge (snapshot/act/query), Retired-Ref Hysteresis, Guarded DOM Marks & WebMCP Tools

**Upstream Repository**: https://github.com/vercel-labs/ui @ `220c1a0d`

## Key Invariants
- **Ref Continuity & WeakRef Memory Safety (`packages/core/src/page/observe/registry.ts#L21-L91`)**: Components track live instances via `WeakRef<PrimitiveInstance>` and preserve refs when unmounted/remounted (such as switching tabs) using a FIFO queue per `component|label|row` key bounded by `retiredLimit = 500`, alongside `offPage` snapshots.
- **DOM Agent Boundary Marks (`packages/core/src/page/observe/marks.ts#L11-L58`)**: `data-agent-hidden` hides subtrees from `snapshot`/`query` and text walks (`isOffLimits`), `data-agent-secret` replaces emitted values with `"[redacted]"` (`isSecret`), and `data-agent-confirm` enforces human confirmation with prompts clipped at `200` characters.
- **Action Surface & Synonyms (`packages/core/src/page/agent/agent.ts#L36-L117`)**: `synonyms` map intuitive commands (`open`/`close`/`show`/`hide` -> `setOpen`, `toggle` -> `setOpen`/`setChecked`/`setPressed`, `select` -> `setValue`) to underlying mutating API verbs.
- **WebMCP Tool Registration (`packages/core/src/page/agent/agent.ts#L1923-L2026`)**: `registerTools` exposes `snapshot`, `act`, and `query` through `document.modelContext.registerTool` with `untrustedContentHint: true`, `consequentialHint` on `act`, and a mandatory per-step `allow` predicate.
