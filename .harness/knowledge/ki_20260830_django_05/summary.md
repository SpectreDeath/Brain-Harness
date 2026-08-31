# Django 6.x Native Background Tasks Architecture & Result Backend Contracts

## Architectural Summary
`django.tasks` introduces first-class background tasks into the framework with pluggable execution backends.

## Operational Guidelines
1. **Task Decorator Standard:** Define background jobs with `@task(queue=...)` for portable execution.
2. **Backend Independence:** Use `ImmediateBackend` for deterministic, zero-dependency unit tests and queue backends (Redis/DB) for production.
3. **Status State Machine:** Track task execution lifecycle via standardized `TaskResultStatus` (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`).
