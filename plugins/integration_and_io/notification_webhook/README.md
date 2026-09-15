# plugin.notification_webhook (v1.0.0)

Webhook notification dispatcher, Slack & Discord card builder, and agent event broadcaster

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/notification_webhook` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.notification_webhook` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `notify_webhook` | `(url, payload, timeout)` | Send a JSON payload to a generic HTTP/HTTPS webhook URL |
| `notify_chat_channel` | `(platform, webhook_url, title, message, status, fields)` | Format and dispatch a rich message card to a Slack or Discord webhook |
| `notify_task_event` | `(event_type, task_name, details, webhook_url)` | Format and broadcast a standardized agent task lifecycle event |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Notification and webhook dispatching plugin for Brain Harness.

#### Classes

- `class NotificationWebhookPlugin` — Harness Plugin providing webhook dispatch, chat cards, and event notifications.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def notify_webhook(url, payload, timeout) -> WebhookDeliveryResult`
  - `def notify_webhook_async(url, payload, timeout) -> WebhookDeliveryResult`
  - `def notify_chat_channel(platform, webhook_url, title, message, status, fields) -> WebhookDeliveryResult`
  - `def notify_chat_channel_async(platform, webhook_url, title, message, status, fields) -> WebhookDeliveryResult`
  - `def notify_task_event(event_type, task_name, details, webhook_url) -> TaskEventResult`
  - `def notify_task_event_async(event_type, task_name, details, webhook_url) -> TaskEventResult`


#### Functions

- `def notify_webhook(url, payload, timeout) -> dict[str, Any]` — Send JSON payload to a target webhook URL.
- `def notify_chat_channel(platform, webhook_url, title, message, status, fields) -> dict[str, Any]` — Format and dispatch a structured notification card to Slack or Discord.
- `def notify_task_event(event_type, task_name, details, webhook_url) -> dict[str, Any]` — Format and broadcast an agent task lifecycle event.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.notification_webhook.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
