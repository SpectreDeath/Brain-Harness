# DSH Superagent: Attention-Minimizing Proactive Agent Philosophy

## Core Principle
> **Take as little human attention as possible, and give as much value as possible.**

Every message, notification, question, setting, and panel element costs human attention and must deliver more value than it consumes (`docs/000-philosophy.md#L5-L7`).

## Decision Heuristics
1. **Explicit or Written-Rule Triggering**: Act only when directly addressed by an allowed person or when a written team rule authorizes proactive action (starting in record-only mode).
2. **Confirm-Work-Resolve Cadence**: Confirm a request once with planned scope, stay quiet during execution, and speak again only for a deliverable, a blocking decision, or a failure.
3. **One Structured Question at a Time**: Surface blocking questions via structured `Attention` fields rather than burying them in long markdown reports.
4. **Stop by Impact, Not Effort**: Local changes proceed to a reviewable PR; architectural/design decisions halt immediately with a concrete question.
