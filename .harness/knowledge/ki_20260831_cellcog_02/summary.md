# KI: Parent Session Tree Fallback DAG & Interim Rewake Heartbeat Delivery

## Operational Summary
In nested multi-agent systems, leaf sub-agents frequently spawn asynchronous cloud tasks and then terminate before the cloud task completes. If notifications are tied strictly to the leaf sub-agent session key, results become orphaned. Implementing a deterministic parental DAG fallback router traverses up the session hierarchy to deliver results safely to the parent or root main session.

## Architecture & Routing Invariants

1. **Deterministic Parental Key Parsing (`get_parent_session_key`)**:
   - Session keys conform to standard structured schemas:
     - `agent:<agentId>:main` → Root session (no parent).
     - `agent:<agentId>:subagent:<u1>` → Resolves parent to `agent:<agentId>:main`.
     - `agent:<agentId>:subagent:<u1>:subagent:<u2>` → Resolves parent to `agent:<agentId>:subagent:<u1>`.
     - `agent:<agentId>:<channel>:<type>:<id>` (e.g. Telegram/Discord) → Resolves to `agent:<agentId>:main`.

2. **Delivery Failover Cascade**:
   - The daemon first attempts direct delivery to the listener session key.
   - If the Gateway API returns `404 Not Found` or `410 Gone` (indicating the ephemeral sub-agent thread has closed), the delivery module walks up the session tree recursively via `get_parent_session_key()` until delivery succeeds at the main agent level.

3. **Multi-Session Seen Index Tracking**:
   - `MessageProcessor` maintains discrete seen-index markers per session per chat in `~/.cellcog/chats/{chat_id}/seen_{session_hash}.json`.
   - Ensures that re-delivering to parent sessions or polling after interim updates only downloads unseen messages and novel attachments, eliminating duplicate file downloads.

## Key References
- Session Routing Logic: [`cellcog_python-main/cellcog_python-main/cellcog/daemon/delivery.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/daemon/delivery.py#L20-L75)
- Message Processor: [`cellcog_python-main/cellcog_python-main/cellcog/message_processor.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/message_processor.py#L30-L90)
- Visual Brief: [data-topology-review-20260831-110000.html](file:///C:/Users/spectre/AppData/Local/Temp/data-topology-review-20260831-110000.html)
