```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: agent-desktop-operator                                        │
│ Category: integration_and_io / desktop-automation                    │
│ Version: 1.1.0                                                       │
│ Invocation: /agent-desktop-operator                                  │
│ Triggers: "operate desktop", "accessibility tree", "snapshot app",   │
│           "click ref", "desktop automation", "agent-desktop"         │
│ Requires: "agent-desktop" CLI or MCP stdio server                    │
│ Target: OS accessibility tree observation, ref action, and recovery │
└──────────────────────────────────────────────────────────────────────┘
```

# Agent Desktop Operator — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **Stage 1: Preflight** | Verify permissions & supported surfaces | `agent-desktop status` | OS accessibility API granted |
| **Stage 2: Skeleton Mapping** | Shallow map with depth clamping | `snapshot --skeleton -i --compact` | Window root & key subtree refs mapped |
| **Stage 3: Subtree Drill-Down** | Expand focused branch | `snapshot --root '@s:eN' -i` | Detailed target refs allocated |
| **Stage 4: Semantic Dispatch** | Act on ref without pointer disruption | `click`, `set-value`, `type` | Action dispatched with disposition |
| **Stage 5: Verify & Recover** | Confirm outcome or handle stale refs | 2D disposition matrix & `wait` | Verified delivery or safe retry |

---

## Vocabulary & Levers

- **Qualified Ref Token**: `@<snapshot_id>:e<N>`. Confined to a single snapshot lifecycle. Bare `@e8` is strictly invalid.
- **Evidence Tri-State**: `Known`, `Absent`, `Unknown`. Never flattened to a binary boolean in negative position.
- **Capture-Proof Uniqueness**: Multi-field bucket verification across the whole window ensuring refs never collide.
- **2D Disposition Matrix**: `DeliveryDisposition` (`NotDelivered`..`DeliveredVerified`) × `RetryDisposition` (`Safe`..`Unsafe`).
- **PowerShell Splatting Guard**: Always single-quote refs (`'@s8f3k2p9:e1'`) in PowerShell to prevent `@` splatting.
- **Web-Wrapper Bypass**: Transparent Chromium containers (`Chrome_WidgetWin_1`) consume zero logical depth.

---

## Mandatory Invariants Checklist

- [ ] **Qualified Ref Enforcement**: Every element reference passed to commands must match `@<snapshot_id>:e<N>`.
- [ ] **PowerShell Quote Escaping**: When running commands in PowerShell, all refs must be single-quoted (`'@s:eN'`).
- [ ] **Headless Semantic Priority**: Prefer headless semantic actions (`Click`, `SetValue`) over physical mouse clicks.
- [ ] **Disposition-Guarded Retries**: Never re-execute a failed action unless its `retry_disposition` is explicitly `safe`.
- [ ] **Subprocess Pipe Drainage**: All asynchronous runner transports must drain stderr into a ring buffer and close pipes in `finally` blocks (Rule 14 & Rule 53).
- [ ] **No Skeleton on Focused Surfaces**: Never apply `--skeleton` to focused overlay surfaces (`menu`, `sheet`, `alert`).
