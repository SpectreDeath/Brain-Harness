# AI-Native Harness Plugin (`plugin.ai_native_harness`)

Domain-partitioned plugin providing production harness governance, 4 behavioral verification gates, credential-free MCP security audits, Git code-to-doc commit drift calculus, and negative query demand mining.

## Features

- **4 Behavioral Verification Gates**: Evaluates static typing (Gate 1), 100% logic coverage (Gate 2), E2E user simulations (Gate 3), and live demo execution (Gate 4), reserving the gate budget for behavior rather than syntax linters.
- **Partial Payload Omission Audit**: Verifies partial update/patch requests do not quietly reset unmentioned fields or permissions.
- **Credential-Free MCP Security**: Validates zero stored credentials, user PAT passthrough, dynamic RBAC, uniform 403 error payloads, identical 404 responses, and SME workflow markers (`[!VERIFY]`, `[!SME]`).
- **Code-to-Doc Drift Calculus**: Measures $\text{Drift Count} = \sum \text{commits modifying } P \text{ since last update of doc } D(P)$, shifting approval badges from green to amber.
- **Negative Query Backlog Mining**: Automatically clusters unanswered assistant queries into prioritized documentation demand.
- **Interactive Visual Briefs**: Synthesizes HTML reports with Mermaid topology diagrams and live telemetry tables.

## Provided Services

- `service.ai_native_harness` (`AI_NATIVE_HARNESS_SERVICE_KEY`)

## Entrypoints

- `four_gates_evaluate(target: str | None)`
- `doc_drift_audit(target: str | None)`
- `mcp_security_audit(config_path: str | None)`
- `negative_backlog_mine(logs_path: str | None)`
- `ai_native_harness_brief(target: str | None, output_path: str | None)`
