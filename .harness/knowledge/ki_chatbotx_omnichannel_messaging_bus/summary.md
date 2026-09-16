# Omnichannel Unified Messaging & Graph Flow Execution Pipeline

## Epistemic Introspection & Overview

Managing conversations across heterogeneous chat ecosystems (Meta Graph API, WhatsApp Cloud API, Telegram Bot API, Zalo OA API, WebSockets) requires normalizing fundamentally incompatible protocols into a coherent domain model.

ChatbotX partitions this complexity across three foundational layers:
1. **Normalized Message & Identity Layer** (`@chatbotx.io/sdk`): Maps channel user identifiers (PSID, phone number, Telegram chat ID) to a unified `Contact` entity with shared tags, custom fields, and bot fields.
2. **DAG Flow Execution Engine** (`@chatbotx.io/flow-config`): Compiles visual node graphs into `CompiledFlow` definitions with discrete node handlers (text, quick replies, buttons, carousels, conditionals, delay timers, and AI prompts).
3. **Asynchronous Distributed Worker Queue** (`apps/worker`, BullMQ + Kafka): Ingests inbound webhooks into event streams, executing flow steps asynchronously to guarantee delivery under rate limits and network degradation.

---

## Anti-Pattern Defenses

- **Direct Channel Coupling**: Code never calls raw vendor HTTP APIs directly; all dispatches route through the integration adapter seam.
- **Synchronous Flow Execution**: Inbound messages are acknowledged to channel webhooks within < 200ms, while flow DAG traversal runs asynchronously via worker jobs.
