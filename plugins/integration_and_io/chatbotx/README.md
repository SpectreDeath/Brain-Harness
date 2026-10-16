# plugin.chatbotx (v1.0.0)

ChatbotX omnichannel messaging, contact management, and visual flow automation bridge

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/chatbotx` |
| Category | `integration_and_io` |
| Isolation Mode | `subprocess` |
| Services Provided | `integration_and_io.chatbotx` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `chatbotx_list_contacts` | `(limit, tag, channel)` | Search and filter contacts across WhatsApp, Telegram, Messenger, and other channels |
| `chatbotx_send_message` | `(contact_id, text, channel)` | Send an outbound text message to a contact on their active channel |
| `chatbotx_trigger_flow` | `(contact_id, flow_id)` | Trigger an automated visual flow DAG for a contact |
| `chatbotx_manage_tags` | `(contact_id, action, tag)` | Add or remove a tag from a contact profile |
| `chatbotx_query_conversations` | `(limit, status)` | List open chat conversations and unread queue counts across channels |
| `chatbotx_broadcast` | `(audience_tag, message_text, channel)` | Dispatch a broadcast message to contacts matching an audience tag |
| `chatbotx_execute_tool` | `(operation_id, parameters)` | Execute a dynamic OpenAPI / MCP tool operation against the ChatbotX API surface |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

ChatbotX omnichannel messaging, contact management, and visual flow automation bridge

#### Classes

- `class ChatbotXPlugin` — Harness Plugin implementing ChatbotX omnichannel integration.
  - `def __init__(config)` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def on_load(context)` — Executes the operation.
  - `def on_unload(context)` — Executes the operation.
  - `def list_contacts(limit, tag, channel)` — Executes the operation.
  - `def get_contact(identifier)` — Executes the operation.
  - `def send_message(contact_id, text, channel)` — Executes the operation.
  - `def trigger_flow(contact_id, flow_id)` — Executes the operation.
  - `def manage_tags(contact_id, action, tag)` — Executes the operation.
  - `def query_conversations(limit, status)` — Executes the operation.
  - `def execute_tool(operation_id, parameters)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.chatbotx.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
