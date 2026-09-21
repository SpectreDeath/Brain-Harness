# Knowledge Item: Harness Engineering for AI-Native Organizations

## Epistemic Distillation

### 1. Paradigm Shift: Trust Inversion from Model to Harness
The conventional paradigm of AI-assisted engineering involves developers prompting an agent, receiving code, manually reading every line of the diff due to distrust, correcting errors, and repeating. Under this dynamic, the AI's generation speed is nullified by the human review bottleneck.

**Harness Engineering** inverts this relationship:
- *"You stop trusting the AI. You start trusting the harness."*
- The engineer's primary job shifts from reading code syntax to designing the environment, operational rules, constraints, and automated verification feedback loops in which the agent operates.
- A single engineer operating within a robust behavioral harness can ship production systems that previously required entire engineering teams.

### 2. The Four Behavioral Verification Gates
Agent code generation errors rarely stem from formatting style; they stem from unexercised logic branches and unverified runtime claims. Gate budgets must prioritize behavior over linters:
1. **Gate 1: Static Type Checker (`tsc --noEmit` / `mypy`)**: Cheapest gate; enforces zero type errors across the entire codebase, catching structural and signature hallucinations.
2. **Gate 2: 100% Core Logic Coverage**: Binary, non-negotiable rule. The agent has no ego; it reads missing coverage reports as an actionable, unambiguous to-do list.
3. **Gate 3: End-to-End User Simulation (Playwright)**: Verifies user-observable behaviors using plain-English assertions rather than testing internal code intent.
4. **Gate 4: Live Runtime Verification & Usage Demo**: The agent must boot the application, verify its changes in live execution, and author a runnable usage demo page exercising the feature.

### 3. The Payload Omission Security Blindspot
A primary failure mode of behavioral gates is testing only the fields carried in an update payload. In partial update endpoints (e.g. document renaming), omitting a security or visibility field can cause it to quietly reset to default permissions (making restricted records public).
- **Invariant**: Automated test contracts must explicitly verify what is *left out* or unstated, asserting that omitted fields preserve their existing security state.

### 4. Zero-Credential Enterprise MCP Architecture
- **Anti-Pattern**: Providing MCP servers with direct database credentials or shared service accounts results in anonymous actions, privilege escalation, and inability to revoke individual access.
- **Enterprise Pattern**: The MCP server holds **zero credentials** and no direct DB connections. It forwards the human user's Personal Access Token (PAT) with every tool call. The backend API validates the user's live role on every request (dynamic RBAC), attributing every action to a real human in the audit log.
- **Leakage Defense**: 403 Forbidden is returned as a clean tool error (`isError: true`); 404 responses return identical messages for non-existent and hidden resources to prevent enumeration attacks.

### 5. Continuous Drift Telemetry & Negative Backlog Mining
- *"You can only improve what you track."* Unmeasured systems decay into neglect; tracked drift becomes an actionable, bounded engineering backlog.
- **Code-to-Doc Drift**: CI maps code paths to documentation assets, turning sign-off badges amber when post-approval code commits occur.
- **Negative Demand Mining**: Unanswered agent questions are logged and clustered into a prioritized backlog of documentation demand, reflecting real user gaps.
- **Human Authority Markers**: `[!VERIFY]` marks agent uncertainty during automated generation; `[!SME]` creates blocking sign-off gates for compliance and financial calculations.
