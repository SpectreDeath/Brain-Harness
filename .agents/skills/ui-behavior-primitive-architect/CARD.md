```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: ui-behavior-primitive-architect                               │
│ Category: software_engineering / ui_architecture                     │
│ Version: 1.0.0                                                       │
│ Invocation: /ui-behavior-primitive-architect                         │
│ Triggers: "definePrimitive", "ui-sdk", "webmcp", "checkPattern",     │
│           "checkServer", "checkDirection", "expert-scope"            │
│ Requires: "agent-harness-architect"                                  │
│ Target: Headless UI primitives, WebMCP bridge & tri-modal checks     │
└──────────────────────────────────────────────────────────────────────┘
```

# UI Behavior Primitive Architect — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Primitive Audit** | `audit_primitive_definition()` | `PrimitiveAuditReport` (`valid`, `root_data_slot`, `violations`) |
| **2. Agent Bridge Gate** | `evaluate_agent_bridge_step()` | `AgentBridgeStepDecision` (`allowed`, `needs_person`, `redacted_value`) |
| **3. Tri-Modal Verify** | `evaluate_tri_modal_check()` | `TriModalVerificationReport` (`aria_passed`, `ssr_passed`, `rtl_passed`) |
| **4. Expert Routing** | `plan_expert_scope()` | `tuple[ExpertScopeRoute, ...]` across 5 frameworks |

---

## Mandatory Invariants Checklist

- [ ] **Kebab Root Naming & Render Prop**: Primitive name must be kebab-case (`root` slot uses `data-slot="<name>"`) and swap elements via `render`, never `as`.
- [ ] **Controlled & Live Isolation**: Never initialize both `<key>` and `default<Key>`, and never place controlled keys inside `live`.
- [ ] **DOM Boundary Redaction**: Hide `data-agent-hidden` subtrees, redact `data-agent-secret` values to `"[redacted]"`, and enforce `data-agent-confirm` (`<= 200` chars).
- [ ] **SSR Clock/Entropy Ban**: Reject any `document`, `window`, `Date.now`, `performance.now`, `Math.random`, or `crypto` access during SSR checks.
- [ ] **Slotted & Frozen Models**: All domain reports use `slots=True, frozen=True` (Rule 12).
