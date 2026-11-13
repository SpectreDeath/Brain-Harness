# Bot HQ: Per-Bot Serial Turn Queue & Bounded Hop-Depth Guard

## Mechanics
- **Serial Turn Queue (`server/src/agent/loop.ts#L25-L50`)**: `enqueue(botId, trigger)` chains onto `queues.get(botId)` so one bot never runs overlapping turns.
- **Approval Supersession**: Incoming user messages immediately call `expireApprovals(botId)` so stale approval cards resolve cleanly as `skipped`.
- **Ping-Pong Cap**: `enqueueBotMessage` propagates `depth` and halts bot-to-bot relays at depth 3.
