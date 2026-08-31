# 4-Tier Hierarchical DI Scopes & Cascade Engine in Agent Frameworks

## Architectural Summary
`@moonshot-ai/agent-core-v2` introduces a 4-tier scoped dependency injection system (`AppScope` $\rightarrow$ `WorkspaceScope` $\rightarrow$ `SessionScope` $\rightarrow$ `AgentScope`) backed by a `CascadeEngine`.

## Operational Guidelines
1. **Scope Invariants:**
   - **AppScope:** Global configurations, telemetry sinks, OAuth token managers, global LLM catalogs.
   - **WorkspaceScope:** Local repository roots, file watchers, git indices, project-level settings.
   - **SessionScope:** Multi-turn transcripts, persistent database connections, session locks.
   - **AgentScope:** Ephemeral ReAct step loops, tool execution fibers, prompt compilations.
2. **Lifecycle Cascade:** Destroying a scope automatically terminates and cleans up all descendant scopes and registered `IDisposable` resources.
3. **No Upward Mutation:** Descendant scopes can read ancestor dependencies, but never mutate ancestor service registrations.
