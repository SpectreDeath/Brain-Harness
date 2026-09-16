┌─────────────────────────────────────────────────────────────┐
│ SKILL: chatbotx                                             │
│ Omnichannel Messaging & Dynamic Automation Engine           │
├─────────────────────────────────────────────────────────────┤
│ Domain: Integration & I/O                                   │
│ Protocol: ChatbotXService (CHATBOTX_SERVICE_KEY)             │
│ Primary Targets: WhatsApp, Telegram, Messenger, Zalo, Web   │
└─────────────────────────────────────────────────────────────┘

## Stage Progression Matrix

| Stage | Name | Binary Completion Gate |
|---|---|---|
| **1. Identity & Scope** | Pre-Flight Resolution | Target contact ID resolved; workspace token validated |
| **2. Channel & Security** | Safety & Hint Evaluation | `x-mcp` hints inspected; mutating actions flagged |
| **3. Checkpoint** | Visual Brief & Plan | HTML brief in `%TEMP%`; checkpoint approved |
| **4. Dispatch & Flow** | Message & Flow Run | Outbound message sent; flow execution enqueued |
| **5. Reconciliation** | Audit & State Check | Delivery status confirmed; contact tags reconciled |

---

## Blocking Invariants

1. **Resolve IDs Before Action** — Never call tagging or flow actions without querying `list_contacts` and resolving verified UUIDs first.
2. **Respect `x-mcp` Safety Hints** — Treat operations flagged with `destructiveHint: true` as mandatory checkpoint stops.
3. **Workspace Token Scope Only** — Filter out channel-token security requirements; only dispatch operations authenticated via workspace developer tokens.
4. **Subprocess Sandbox Execution** — Execute user-submitted JavaScript steps inside isolated microservices (`isolated-vm`), never inside the main proactor.
5. **Local String Salvage** — Strip markdown fences and remove trailing commas before paying reprompt tokens on raw model responses.

---

## Vocabulary & Key Concepts

- **ContactRecord**: Slotted immutable entity unifying channel user identities (PSID, phone number, handle) under a single contact profile.
- **CompiledFlow**: Deterministic DAG representation of visual chatbot nodes (text, condition, action, webhook, AI prompt).
- **oRPC Dynamic Reflection**: Architecture where TypeScript routers automatically compile into OpenAPI 3.1 specs with first-class MCP tool hints.
- **Isolate Sandbox**: Lightweight V8 heap instance executing flow transformations with strict memory and CPU runtime quotas.
