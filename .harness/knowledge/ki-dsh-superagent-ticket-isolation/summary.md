# DSH Superagent: Per-Ticket Execution Isolation & Serialized Channel Replies

## Key Invariants
1. **Per-Ticket Isolation**: Workers run in their own session and directory and can only read their own Ticket, subscribed Threads, and originating Triggers.
2. **Ordered Outbox Delivery**: Replies for the same `(Ticket, Conversation)` are strictly ordered so acknowledgements go out before results; unrelated tickets do not block each other.
3. **Crash/Restart Recovery**: Interrupted running assignments restart with a recovery note instructing the worker to inspect its directory, git history, and GitHub before repeating external side effects.
