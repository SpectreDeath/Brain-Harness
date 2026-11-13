# DSH Superagent: Synchronous Hexagonal Core & Transactional Outbox

## Pattern
- **Synchronous Core (`src/core/engine.ts#L25-L88`)**: All domain transitions execute synchronously inside `repo.atomic(() => ...)`, eliminating async race conditions on Ticket/Thread state.
- **Transactional Outbox (`src/core/ports.ts#L50-L120`)**: Ports (`Assessor.request`, `Executor.start/deliver/stop`, `Outbox.send`) enqueue durable side effects inside the same transaction.
- **Coalesced Passes (`src/app/passes.ts#L22-L68`)**: `Passes.pump()` serializes effect kicking and `Engine.evaluateDue()`, coalescing concurrent triggers into a single follow-up pass.
