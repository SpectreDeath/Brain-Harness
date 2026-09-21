---
name: ai-native-harness-engineer
description: Architect, construct, and govern production AI coding harnesses using 4-gate behavioral pipelines, credential-free MCP security, and continuous drift telemetry. Do not use for generic prompt writing, superficial AST style linting, or unauthenticated shared database backdoors.
---

# AI-Native Harness Engineer: Production Coding & Governance Playbook

`ai-native-harness-engineer` is the procedural engineering and organizational governance engine for transforming development teams into AI-native engineering organizations. Synthesized from Tech With RJ's foundational literature (*How I Used Harness Engineering to Make Our Company AI-Native*, freeCodeCamp, Sept 2026), this skill operationalizes the core axiom of autonomous software development: **"You stop trusting the AI. You start trusting the harness."**

When software teams adopt AI coding agents, velocity frequently evaporates because engineers manually inspect and second-guess every line of generated diffs. `ai-native-harness-engineer` inverts this bottleneck. Instead of reviewing syntax, engineers design the **behavioral verification harness**—a four-gate pipeline, an enterprise Model Context Protocol (MCP) server holding zero credentials, a repo rules file with a graveyard of rejected ideas, and automated telemetry tracking documentation drift and negative demand backlogs.

Every harness engineering implementation executes this five-stage progression:

```
[1. Scoping & Baseline Telemetry] → [2. Repo Rules & Graveyard] → [3. Four Behavioral Gates] → [4. Credential-Free MCP Bridge] → [5. Drift Telemetry & Backlog Mining]
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage reference matrix, and quality checklist.
Consult [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for harness runtime selection, [../codebase-context-architect/SKILL.md](../codebase-context-architect/SKILL.md) for multi-layer rules management, and [../deterministic-validation-loop/SKILL.md](../deterministic-validation-loop/SKILL.md) for deterministic spec validation.

---

## 1. Process Scoping & Baseline Telemetry

Isolate a high-friction, bounded workflow and establish measurable drift baselines before introducing coding agents:

1. **Target Selection (The Anti-Mandate Rule)**:
   - Target one high-friction, low-risk operational workflow that currently annoys engineers (e.g. stale system documentation, manual ticket triage, release note synchronization, PR validation summaries).
   - Reject high-risk, uncontained rewrites or strategic architectural overhauls as initial harness pilots.
   - Restrict the pilot to a single internal team boundary where data stays in-house and team members provide immediate feedback.
2. **Data Structuring & Ownership**:
   - Transform informal, scattered communication (Slack chats, emails, unrecorded standups) into structured, timestamped records.
   - Assign every operational asset an explicit human owner and an authoritative source path.
3. **Establish Baseline Staleness Metrics**:
   - Define a concrete formula for drift:
     $$\text{Drift Count} = \sum \text{Code commits modifying path } P \text{ since last update of doc } D(P)$$
   - Log the baseline staleness and cycle time so that subsequent agent improvements are proved by empirical numbers rather than qualitative slide decks.

> **Completion criterion**: Bounded operational workflow selected, structured ownership schema established, and baseline drift metric recorded.

---

## 2. Repo Rules & Graveyard Formulation

Construct the immutable contextual scaffolding that guides agent code generation across all turns:

1. **System Architecture & Operational Recipes**:
   - Author a lean repository instruction file (`AGENTS.md` / `CLAUDE.md`) defining the non-negotiable tech stack, directory layouts, and step-by-step recipes for every feature.
   - Enforce bounded context rules (<150 lines) to prevent prompt bloat and context blowout.
2. **The Graveyard of Rejected Ideas**:
   - Explicitly document previously tested, failed, or prohibited design patterns along with the technical rationale for their rejection.
   - Force every fresh agent session to ingest this graveyard to prevent agents from re-proposing previously discarded or invalid solutions.
3. **Seam Definition & Negative Boundaries**:
   - Declare strict boundaries defining files and directories that the agent must NEVER modify (e.g., vendor caches, production database seeds, authentication kernels).

> **Completion criterion**: Rules file authored containing architecture recipes, explicit negative boundaries, and a populated graveyard of rejected ideas.

---

## 3. The Four Behavioral Gates

Construct the non-negotiable, four-gate automated verification pipeline. Allocate the entire validation budget to verifiable runtime behavior rather than superficial AST style linters:

1. **Gate 1: Static Type Checker (`tsc --noEmit` / `mypy`)**:
   - Run complete, strict static type checking across the entire repository.
   - Enforce zero type errors; reject any change with type coercion hacks (`as any`, `shoehorn` violations). Catches signature mismatches and missing properties immediately at zero runtime cost.
2. **Gate 2: 100% Core Logic Coverage**:
   - Enforce binary 100% line, branch, and function coverage on core business logic.
   - Treat coverage reports as an objective, non-negotiable to-do list for the agent: an uncovered branch mandates an additional unit test.
3. **Gate 3: End-to-End User Simulation (Playwright)**:
   - Execute an automated browser or API test suite simulating authentic user workflows.
   - Author assertions in plain-English user-observable states (e.g., "page displays confirmation badge", "dialog closes") rather than internal implementation details.
4. **Gate 4: Live Runtime Verification & Feature Usage Demo**:
   - Mandate that the agent boot the live application or test server and observe the exact behavior it claims to have changed.
   - Require the agent to author a short, runnable feature usage demo page or script exercising the feature in practice. Proves behavioral claims beyond passing unit tests.
5. **The Partial Payload Omission Audit**:
   - Adversarially inspect update and patch endpoints to ensure partial payloads do NOT quietly reset unmentioned fields (such as visibility or security scopes) to defaults.

> **Completion criterion**: All four gates automated in CI and local test runners; 100% logic coverage enforced; feature usage demo authored.

---

## 4. Deploy Credential-Free MCP Security Bridge

Expose application tools and operational data to AI agents using the Model Context Protocol (MCP) without compromising enterprise security:

1. **Zero Stored Credentials Architecture**:
   - Ensure the MCP server holds zero database credentials, zero service keys, and zero master tokens.
   - Forward the human user's Personal Access Token (PAT) with every tool invocation.
2. **Server-Side Dynamic RBAC**:
   - Require the backend API to evaluate role-based access control (RBAC) dynamically on every tool execution against the user's active role.
   - Ensure role revocation or group privilege changes take effect instantaneously without re-minting or tracking down tokens.
3. **Uniform Error Sanitization & Leakage Defense**:
   - Catch 403 Forbidden responses and return clean, structured error payloads (`isError: true, text: "Error: Forbidden."`).
   - Return an identical 404 response (`No document: {slug}`) for both non-existent resources and restricted resources the user lacks permission to see, preventing enumeration attacks.
4. **Human Authority Workflow Markers**:
   - Implement inline `[!VERIFY]` markers for agent-flagged uncertainties during automated drafting.
   - Implement `[!SME]` sign-off gates for compliance, financial rates, or security-sensitive paths, blocking merge/approval until an authorized subject matter expert signs off.

> **Completion criterion**: MCP server operational holding zero credentials, user PAT forwarding verified, dynamic RBAC enforced, and 403/404 errors sanitized.

---

## 5. Activate Negative Telemetry & Agent Bottleneck Mining

Harness the compounding intelligence of the AI-native feedback loop:

1. **Negative Query Demand Mining**:
   - Instrument the AI assistant to log every query it cannot answer with certainty.
   - Cluster and rank unanswered questions into an automated backlog of documentation demand, reflecting actual user information gaps.
2. **CI Code-to-Doc Drift Triggers**:
   - Map code repository paths to documentation slugs.
   - When a commit modifies code paths associated with a document, CI automatically increments the drift count and transitions approval badges from green to amber.
3. **Document Health Scoring**:
   - Maintain a composite health score per document (based on days since last edit, code drift count, and user feedback).
   - Generate automated weekly digests alerting document owners to decaying assets.
4. **Agent-Assisted Bottleneck Auditing**:
   - Regularly query the agent against accumulated operational telemetry:
     * *"Where is work piling up across current PRs?"*
     * *"Which step in the approval cycle has the highest wait time?"*
     * *"Which documented APIs have experienced the highest code churn without documentation updates?"*

> **Completion criterion**: Unanswered queries transformed into prioritized backlog; CI drift triggers active; automated health scores computed.

---

## The Visual Brief Pillar

Whenever architecting or reforming an operational harness, synthesize the 5-stage lifecycle DAG, 4 behavioral gates, and MCP security topology into an interactive HTML visual brief:

1. **Target File Location**: Render the report into `%TEMP%\harness-brief-<timestamp>.html` (or `/tmp/` on Unix).
2. **Interactive Elements**: Embed dark-theme Mermaid.js diagrams illustrating the four behavioral gates and the credential-free token flow.
3. **Telemetry Dashboard**: Include live tables of drift counts, doc health scores, and ranked negative query backlogs.
4. **Delivery**: Present the absolute, clickable link to the user before code execution.

---

## Mandatory Checkpoint Gate

Prevent ungrounded or unchecked mutations to the production system:

1. **Implementation Plan Gate**: Before modifying repository configuration, CI pipelines, or MCP servers, author an `implementation_plan.md` artifact specifying proposed changes, boundary definitions, and testing gates.
2. **Explicit User Sign-Off**: Set `RequestFeedback: true` in artifact metadata. STOP and wait for explicit human review before applying destructive or wide-ranging state changes.
3. **SME Authority Invariant**: Any modification touching compliance, financial calculations, or authentication boundaries requires a mandatory checkpoint sign-off from an authorized human reviewer.

---

## Diagnostic Coaching Rubrics

### Trust Inversion & Gate Allocation Rubric
- **Level 1 (Failing - Score < 5)**: Engineers spend 80% of their time reading agent diffs line-by-line; tests are spotty; linting errors fail builds while logic branches remain untested.
- **Level 2 (Transitional - Score 6-8)**: Type checker and unit tests pass, but end-to-end tests are missing; engineers must manually run and verify features; agent re-proposes rejected designs.
- **Level 3 (AI-Native - Score 9-10)**: 4 automated gates enforce 100% logic coverage and live execution; rules file maintains a graveyard of rejected patterns; engineers only review high-level boundaries and live demonstrations.

### Enterprise MCP Security Rubric
- **Level 1 (Failing - Score < 5)**: MCP server connects directly to the database via root/shared credentials; actions are anonymous; 404 responses reveal hidden document titles.
- **Level 2 (Transitional - Score 6-8)**: Token authentication is present but relies on a shared service account; role revocation requires restarting the MCP server.
- **Level 3 (AI-Native - Score 9-10)**: MCP server holds 0 credentials; forwards user PATs; live RBAC checks on every call; actions attributed to real individuals in audit trails; identical 404 responses eliminate resource enumeration.

---

## Micro-Kernel IoC & Headless CLI Seams (Rule 49 & Rule 10)

`ai-native-harness-engineer` is elevated into the Harness micro-kernel with typed IoC service keys, domain plugin entrypoints, and headless Click CLI commands:

### 1. In-Memory Service Resolution (Rule 49)
```python
from harness.services import AI_NATIVE_HARNESS_SERVICE_KEY

# Resolve authoritative service from IoC container
harness_service = context.require(AI_NATIVE_HARNESS_SERVICE_KEY)

# Run 4 behavioral verification gates
gates = harness_service.evaluate_gates()

# Calculate code-to-doc commit drift
drift = harness_service.calculate_code_to_doc_drift()

# Audit credential-free MCP security
mcp_check = harness_service.audit_mcp_security()

# Mine unanswered queries into documentation demand
backlog = harness_service.mine_negative_backlog()
```

### 2. Headless Click CLI Seams (Rule 10)
```powershell
# Run comprehensive audit across all 3 pillars
harness gate audit [--target <dir>] [--json]

# Evaluate the 4 behavioral verification gates
harness gate evaluate [--target <dir>] [--json]

# Audit MCP server posture for zero credentials & leak defense
harness gate mcp [--config <path>] [--json]

# Calculate Git code-to-doc commit drift
harness gate drift [--target <dir>] [--json]

# Mine negative assistant queries into demand backlog
harness gate mine [--logs <path>] [--json]

# Generate interactive HTML visual brief
harness gate brief [--output <path>] [--no-open]
```

### 3. Domain Plugin Tool Entrypoints (Rule 45)
Registered under `plugins/agent_orchestration/ai_native_harness`:
- `four_gates_evaluate`: Executes Gate 1-4 pipeline.
- `doc_drift_audit`: Runs Git code-to-doc drift calculations.
- `mcp_security_audit`: Asserts zero-credential MCP posture.
- `negative_backlog_mine`: Clusters unanswered queries.
- `ai_native_harness_brief`: Renders HTML visual brief.

---

## Anti-Patterns

- **Line-Review Bottleneck** — Reading and fixing every line of agent output by hand because you don't trust the model.
- **Shared Credential Backdoor** — Connecting agents to databases using shared service keys, creating anonymous privilege escalation.
- **Payload Omission Blindspot** — Testing only what a payload carries, allowing unmentioned fields to quietly reset to defaults.
- **Style-Gate Misallocation** — Spending gate and token budgets enforcing AST linting/formatting while skipping live runtime verification.
- **Silent Drift Decay** — Letting documentation quietly rot by failing to link code paths to documentation owners and omitting automated staleness telemetry.
- **Untracked Knowledge Gap** — Discarding failed or unanswered agent queries instead of capturing them as a ranked demand backlog.
