# Quick Start Guide: `plugin.notification_webhook` (v1.0.0)

> Webhook notification dispatcher, Slack & Discord card builder, and agent event broadcaster

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`notify_webhook`**: Send a JSON payload to a generic HTTP/HTTPS webhook URL
- **`notify_chat_channel`**: Format and dispatch a rich message card to a Slack or Discord webhook
- **`notify_task_event`**: Format and broadcast a standardized agent task lifecycle event

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.notification_webhook.notify_webhook', {'url': '<url>', 'payload': '<payload>', 'timeout': '<timeout>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.notification_webhook
harness plugin enable plugin.notification_webhook
```

## ⚡ Available Entrypoints & Skills
- **`notify_webhook(url: string, payload: object, timeout: number)`**
  Send a JSON payload to a generic HTTP/HTTPS webhook URL
- **`notify_chat_channel(platform: string, webhook_url: string, title: string, message: string, status: string, fields: object)`**
  Format and dispatch a rich message card to a Slack or Discord webhook
- **`notify_task_event(event_type: string, task_name: string, details: object, webhook_url: string)`**
  Format and broadcast a standardized agent task lifecycle event