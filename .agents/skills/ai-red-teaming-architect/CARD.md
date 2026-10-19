```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        ai-red-teaming-architect                 │
│ Category:     security_and_forensics                   │
│ Invocation:   /ai-red-teaming-architect                │
│ Triggers:     "pyrit scan", "red-teaming", "jailbreak",│
│               "prompt injection", "adversarial audit"  │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.pyrit_scanner"                  │
├────────────────────────────────────────────────────────┤
│ Target:       Execute automated GenAI adversarial      │
│               red-teaming, jailbreak audits, and       │
│               vulnerability scorecard synthesis.       │
└────────────────────────────────────────────────────────┘
```

# AI Red-Teaming Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Target Scoping** | Select target type (agent_loop, system_prompt, tool_interface) | `target_spec.json` | Target type verified in allowed catalog |
| **2. Attack Vectoring**| Select technique (crescendo, jailbreak, fuzz) and intensity | `vector_config.json` | Intensity strictly bounded between 1 and 5 |
| **3. Subprocess Probe**| Dispatch probes via lazy venv runner with pipe drainage | `raw_probe_traces.json`| Zero orphaned pipes; loopback preserved |
| **4. Scorecard Output**| Synthesize attack success rate, risk level, and fixes | `scorecard_report.json` | Normalized risk level (low/medium/high/critical) |

---

## Mandatory Invariants Checklist

- [ ] **Lazy Venv Staging Invariant**: Heavy dependencies (pyrit, azure-ai) must remain uninstalled in base env; staging is lazy on first invoke.
- [ ] **Pipe Drainage Invariant**: All subprocess transports must drain stdout/stderr and close stdin in a `finally` block.
- [ ] **Loopback Preservation Invariant**: Network interception hooks must preserve local loopback `127.0.0.1` and `::1`.
- [ ] **Slotted Scorecard Invariant**: Vulnerability scorecards must adhere to `@dataclass(slots=True, frozen=True)` schemas.
