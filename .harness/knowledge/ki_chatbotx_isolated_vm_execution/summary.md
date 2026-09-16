# Multi-Tenant Microservice Sandbox Execution via isolated-vm

## Epistemic Introspection & Overview

Chatbot visual flows frequently require custom transformation logic (parsing external webhook JSON payloads, formatting dynamic dates, computing discount rates). Allowing user-submitted JavaScript code to execute inside the main Node.js process risks:
1. Prototype pollution and global state tampering
2. Infinite loops blocking the Node.js event loop
3. Memory leakage crashing worker containers
4. Unauthorized filesystem or network exfiltration

ChatbotX solves this by isolating execution into a dedicated **JavaScript Executor Service** (`apps/javascript-executor`) that runs client code inside isolated V8 isolates (`isolated-vm`).

---

## Architectural Topology

```
[Visual Flow Engine] (apps/worker or apps/builder)
        │
        ▼ (HTTP JSON-RPC / contract)
[@chatbotx.io/javascript-sandbox Client]
        │
        ▼
[javascript-executor Microservice]
        │
        ▼
[isolated-vm V8 Isolate]
  ├── Heap Limit: 32MB / 64MB
  ├── Timeout Guard: 500ms - 2000ms
  ├── Sanitized Globals: { variables, input, console.log }
  └── No Node.js Builtins: (no fs, net, child_process)
```

### Invariants:

- **Decoupled Process Boundary**: Native V8 C++ addons (`isolated-vm`) are restricted to the executor microservice, keeping the builder web app purely portable.
- **Resource Sandboxing**: Each script runs in a disposable `ivm.Isolate` with an isolated microtask queue and rigid wall-clock execution limits.
