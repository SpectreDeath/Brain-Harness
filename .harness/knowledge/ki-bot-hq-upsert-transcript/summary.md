# Bot HQ: Append-Mostly `(seq, updatedSeq)` Upsert Transcript Model

## Design
- **Idempotent Streaming Upserts**: A streaming reply or evolving tool-call row keeps its `seq` and increments `updatedSeq`, allowing browser clients to upsert cleanly from SSE (`GET /api/events`).
- **Session Generation Reset**: Incrementing a bot's `generation` starts a fresh conversation and fresh underlying Hermes session without mutating historical rows.
