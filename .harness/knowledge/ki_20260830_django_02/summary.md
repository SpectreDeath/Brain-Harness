# WeakRef Signal Dispatcher Pattern with Dead-Receiver GC

## Architectural Summary
`django.dispatch.Signal` implements a high-performance publish-subscribe bus with automatic weakref cleanup.

## Operational Guidelines
1. **WeakRef Receiver Storage:** Use `weakref.ref` for functions and `weakref.WeakMethod` for bound instance methods.
2. **Automatic Pruning:** Sweep dead references automatically during dispatch when dead weakrefs return `None`.
3. **Async / Sync Resilience:** Use `send_robust` and `asend_robust` to catch receiver exceptions without crashing the primary execution pipeline.
