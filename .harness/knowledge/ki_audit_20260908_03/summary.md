## Blast Radius Registry — Critical Seam Nodes

### CRITICAL (affects entire stack)
1. **ServiceContext** (kernel/context.py) — ALL 125 src files, ALL 137 plugins
2. **PluginLifecycleManager** (kernel/lifecycle.py) — plugin FSM, loader, sandbox transport

### HIGH (affects agent execution)
3. **StepExecutionEngine** (agent/react.py) — all tool invocations, git checkpoints, lint loop
4. **SwarmCoordinator** (agent/swarm.py) — wave ordering, session manager, consensus voting
5. **ToolRegistry** (services/tools.py) — ~80% of domain plugins, interceptor telemetry chain

### Verified By
- 1,103 passing tests across 173 test files (2026-09-08 audit run)

### Protocol
Before modifying any CRITICAL or HIGH node:
1. Run full pytest suite and record baseline
2. Map all transitive import dependents via grep
3. Author failing test contract against seam
4. Execute change with atomic git checkpoint
