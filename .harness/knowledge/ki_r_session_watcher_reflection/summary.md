# Non-Invasive User-Space Session Introspection & Workspace Tracking

## Context & Theoretical Grounding
To display live variables, active data frames, loaded packages, and help docs without halting or altering user scripts, an editor extension must observe R's runtime state unobtrusively.

## Distilled Mental Models & Heuristics
1. **Task Callback Hook Injection**:
   - `init.R` registers an `addTaskCallback()` in R. Upon the completion of top-level user evaluations, R automatically triggers the `.vsc.attach()` callback hook.
2. **Isolated Environment Encapsulation**:
   - All reflection logic lives inside an isolated parent environment (`.vsc`), preventing symbol collisions with user variables in `.GlobalEnv`.
3. **Atomic Watcher State Export**:
   - Session data (`globalenv.json`, `packages.json`, `capabilities.json`) is atomically written to a session-specific directory (`pid_dir`) and consumed by `session.ts` in VS Code to refresh workspace views, data tables, and plot view columns.

## Anti-Pattern Defenses
- **GlobalEnv Mutation**: Polluting the user's workspace with utility functions or metadata variables.
- **Blocking REPL Polling**: Continuously executing inspection queries in the user's interactive console, interrupting active readline loops.
