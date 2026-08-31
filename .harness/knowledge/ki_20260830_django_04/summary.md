# Transactional Atomic Savepoint Stacks & Multi-Database Router Isolation

## Architectural Summary
`django.db.transaction.atomic` implements nested savepoint management for ACID reliability.

## Operational Guidelines
1. **Savepoint Nesting:** Use database savepoints (`SAVEPOINT`) for nested transaction scopes so sub-operations can fail and recover independently.
2. **Exception Safety:** Always wrap rollbacks in `try...finally` blocks to ensure uncorrupted connection return to connection pools.
3. **Router Awareness:** Dispatch read and write queries according to multi-database routing rules to prevent split-brain states.
