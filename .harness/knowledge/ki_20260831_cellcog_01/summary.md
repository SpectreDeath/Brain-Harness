# KI: Zero-Footprint Asynchronous Daemon & WebSocket-to-Polling State Machine

## Operational Summary
Asynchronous sub-agent operations requiring minutes or hours of cloud processing should not hold blocking client SDK sockets or maintain permanent host daemon processes. By separating the client interface from a transient background daemon that auto-terminates on empty queues, agent harnesses achieve non-blocking fire-and-forget concurrency without persistent memory leaks.

## Protocol & Architecture Invariants

1. **Ephemeral Daemon Lifecycle (`cellcog-daemon`)**:
   - `CellCogClient` initiates work by writing tracking files to `~/.cellcog/tracked_chats/{chat_id}.json` and spawning a detached daemon process via `subprocess.Popen(["cellcog-daemon", ...])`.
   - The daemon monitors active chats, and once all tracked chats transition to terminal states (`CHAT_COMPLETED` or fatal error), the daemon automatically executes a graceful self-shutdown (`sys.exit(0)`).
   - Subsequent SDK calls cleanly spawn a fresh daemon running the latest on-disk code, preventing stale daemon drift.

2. **Dual-Channel State Machine (WebSocket + Fallback Polling)**:
   - Primary: High-throughput asynchronous WebSocket listener (`ws_healthy = True`).
   - Secondary: Automated fallback to bulk status REST polling (`/cellcog/chat/status/bulk`) at configurable intervals (e.g. 30s) if the WebSocket encounters transport disruption.

3. **Interim Update Broadcaster (Anti-Timeout Heartbeat)**:
   - For long-running cloud tasks (such as 1080p video rendering or 3D mesh synthesis), the daemon maintains a rolling queue of progress events and broadcasts interim updates every ~4 minutes (`interim_update_interval = 240s`).
   - This prevents host agent framework timeouts (e.g. OpenClaw/Cursor idle watchdog triggers) before the final deliverable is ready.

## Key References
- Source Code: [`cellcog_python-main/cellcog_python-main/cellcog/daemon/main.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/daemon/main.py#L30-L120)
- Client Driver: [`cellcog_python-main/cellcog_python-main/cellcog/client.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/client.py#L40-L115)
- Visual Brief: [data-topology-review-20260831-110000.html](file:///C:/Users/spectre/AppData/Local/Temp/data-topology-review-20260831-110000.html)
