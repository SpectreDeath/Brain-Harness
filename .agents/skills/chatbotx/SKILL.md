---
name: chatbotx
description: Orchestrate omnichannel chatbot workflows, contact identity tags, DAG flows, and dynamic OpenAPI tools across WhatsApp, Telegram, and Messenger. Do not use for raw local database administration or unauthenticated webhook injection.
---

# ChatbotX: Omnichannel Messaging & Dynamic Automation Engine

`chatbotx` is the production agent skill for interacting with, automating, and orchestrating the ChatbotX platform across 26 messaging and CRM channels (WhatsApp, Messenger, Telegram, Zalo, Instagram, Webchat, TikTok, Email).

It provides deterministic contact identity resolution, message dispatch, visual flow DAG execution, broadcast scheduling, and dynamic oRPC OpenAPI / MCP tool introspection.

Every ChatbotX workflow follows a five-stage progression:

```
[1. Identity & Scope Resolution] ──► [2. Channel & Security Pre-Flight] ──► [3. Interactive Action Checkpoint]
                                                                                        │
                                                                                        ▼
[5. Audit Log & State Reconciliation] ◄── [4. Dispatch, Flow & Tool Execution] ◄───────┘
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and blocking invariants.
Consult [config.default.yaml](config.default.yaml) for operational budgets, timeout bounds, and zero-fork overrides.
Reference [eval_matrix.json](resources/eval_matrix.json) for 2x2 continuous evaluation test cases.

---

## The 5-Stage ChatbotX Progression

### 1. Identity & Scope Resolution
Resolve target contact, channel identifier, and workspace credentials before executing state mutations:
1. **Resolve Contact Identity**:
   - Query contacts using `chatbotx_list_contacts(tag=..., channel=...)` or CLI `contacts list`.
   - Never assume IDs; resolve both `contactId` and associated `tagId` or `flowId` prior to invocation.
2. **Determine Channel Protocol**:
   - Identify the recipient's primary channel (e.g. `whatsapp`, `telegram`, `messenger`, `zalo`).
   - Verify that the target channel is active and connected in the workspace.

> **Completion gate**: Target contact ID resolved, channel verified, and workspace credentials validated.

---

### 2. Channel & Security Pre-Flight
Verify operational constraints, rate limits, and safety boundaries:
1. **Evaluate MCP & OpenAPI Hints**:
   - Check `x-mcp` metadata hints (`readOnlyHint`, `idempotentHint`, `destructiveHint`).
   - If an operation is marked `destructiveHint: true` (e.g. bulk broadcast, contact deletion, unblock), require explicit checkpoint confirmation.
2. **Enforce Workspace-Token Scope**:
   - Assert that operations use workspace-level tokens (`bearerAuth`, `developerAccessToken`).
   - Reject unauthenticated channel webhook invocations.

> **Completion gate**: Operation classified as read-only or mutating; parameter schemas validated.

---

### 3. Interactive Action Checkpoint
Provide visual transparency and enforce human confirmation for mutating workflows:
1. **Render Visual Brief (%TEMP%)**:
   - When executing high-impact workflows (broadcast campaigns, multi-step flow triggers), scaffold an HTML brief in `%TEMP%\chatbotx-action-<timestamp>.html`.
   - Display target audience count, channel distribution, and DAG flow diagram.
2. **Present Checkpoint Plan**:
   - Present proposed changes in `implementation_plan.md` with `RequestFeedback: true`.
   - Await explicit user confirmation before dispatching outbound broadcasts.

> **Completion gate**: Visual brief rendered to %TEMP% and user approval recorded.

---

### 4. Dispatch, Flow & Tool Execution
Execute the requested operation through the micro-kernel service or sandboxed plugin:
1. **Execute Outbound Transmission**:
   - Dispatch message via `chatbotx_send_message(contact_id=..., text=...)`.
   - Enqueue DAG flow execution via `chatbotx_trigger_flow(contact_id=..., flow_id=...)`.
2. **Local String Salvage**:
   - If dynamic tool outputs return raw markdown fences or trailing commas, run deterministic local string salvage before reprompting.

> **Completion gate**: Outbound message or flow execution returned with verified status (`sent`, `enqueued`, or `success`).

---

### 5. Audit Log & State Reconciliation
Verify state convergence and capture diagnostic audit logs:
1. **Inspect Conversation & Message Queue**:
   - Verify conversation status and unread counters via `chatbotx_query_conversations()`.
   - If an asynchronous flow step fails, inspect `error-logs list` for execution exceptions.
2. **Reconcile Contact Tags & Variables**:
   - Verify that post-flow tags and custom field updates are reflected on the contact record.

> **Completion gate**: Conversation state updated, delivery acknowledged, and telemetry recorded.

---

## Three Foundational Pillars

### 1. The Visual Brief
Every multi-contact broadcast or complex flow deployment must render an interactive HTML brief in `%TEMP%` detailing audience criteria, message templates, and Mermaid DAG flows before execution.

### 2. The Mandatory Checkpoint
Mutating actions—such as bulk tagging, contact deletion, broadcast triggering, or flow reassignments—must halt at an explicit `implementation_plan.md` checkpoint with `RequestFeedback: true`.

### 3. Explicit Anti-Patterns
Rigid operational boundaries prevent token burnout, 401 cascade failures, and unauthenticated API leaks.

---

## Anti-Patterns

- **ID Assumption Blindness** — Attempting to tag or message a contact using an unverified raw string name without first resolving `contactId` and `tagId` via search.
- **Unchecked Broadcast Blast** — Dispatched bulk messages to an entire workspace without audience segmentation, pre-flight rate check, or interactive approval.
- **Security Scope Mismatch** — Calling channel-token API endpoints with workspace tokens, resulting in predictable 401 unauthorized errors.
- **Synchronous Flow Blocking** — Polling long-running DAG subflows in tight synchronous loops rather than inspecting asynchronous task queues.
- **Unsalvaged Reprompt Loop** — Resending full agent prompts on minor JSON formatting glitches instead of applying fast local regex string salvage.
