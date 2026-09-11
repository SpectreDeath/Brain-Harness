# Bridge Architecture: Subprocess Sandboxing & Diátaxis Framework

## 1. Subprocess Sandbox Architecture (Rule 5, Rule 7, Rule 14)
External or untrusted GitHub plugins run in subprocess sandboxes communicating via JSON-RPC stdin/stdout pipes:

```
┌─────────────────┐       JSON-RPC over Pipes      ┌─────────────────────────┐
│ Harness Kernel  │ ◄────────────────────────────► │ Subprocess Sandboxed    │
│ (In-Process)    │   (stdin / stdout drained)     │ Plugin Virtualenv       │
└─────────────────┘                                └─────────────────────────┘
```

### Transport Pipe Invariant (Rule 14)
```python
try:
    stdout, stderr = await process.communicate(input=request_bytes)
finally:
    if process.stdin and not process.stdin.is_closing():
        process.stdin.close()
```

## 2. Diátaxis 4-Quadrant Documentation Framework
The Diátaxis documentation model splits documentation across two axes:

| | Practical (Action-Oriented) | Theoretical (Knowledge-Oriented) |
|---|---|---|
| **Learning Steps** | **Tutorial**: Learning path for newcomers | **Explanation**: Architecture, design decisions, trade-offs |
| **Working Needs** | **How-To Guide**: Step-by-step solutions to real tasks | **Reference**: Exact API signatures, specs, keys |

## 3. C4 Architecture Modeling
- **Level 1 (System Context)**: Interaction with users and external services.
- **Level 2 (Containers)**: Executable processes, subprocess sandboxes, databases.
- **Level 3 (Components)**: Individual classes, service interfaces, event dispatchers.
