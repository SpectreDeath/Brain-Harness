# Quick Start Guide: `domain.hermes_gateway_relay`

## 🎯 When to Use
Use this plugin to dispatch multi-platform notifications, stream WebSocket telemetry, and control serverless scale-to-zero hibernation.

## 🛠️ Available Entrypoints
- `dispatch_platform_message(platform, channel_id, text)`
- `stream_ws_telemetry(session_id, event_payload)`
- `manage_scale_to_zero(idle_timeout_seconds)`
