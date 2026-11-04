```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: agent-desktop                                                 │
│ Category: integration_and_io                                         │
│ Invocation: @tool or ServiceKey                                      │
│ Version: 1.1.0                                                       │
│ Isolation: subprocess                                                │
│ Provides: "service.agent_desktop"                                    │
│ Target: OS accessibility tree observation, ref actions, and recovery │
└──────────────────────────────────────────────────────────────────────┘
```

# Agent Desktop Plugin Summary Card

## Tool Matrix

| Tool | Purpose | Primary Inputs |
|---|---|---|
| `desktop_snapshot` | Observe app accessibility tree or drill into root ref | `app`, `root_ref`, `interactive_only`, `skeleton`, `compact` |
| `desktop_act` | Execute semantic or physical action on ref | `action`, `ref_id`, `value`, `headed`, `interval_ms` |
| `desktop_find` | Search accessibility tree by role, name, or text | `app`, `role`, `name`, `text` |
| `desktop_manage_window` | List, focus, resize, or move windows | `operation`, `app`, `window_id`, `bounds` |
| `desktop_wait` | Wait for UI condition without fixed sleep races | `app`, `element_ref`, `window_title`, `text`, `timeout_ms` |
| `desktop_status` | Check platform API status and permissions | `check_permissions` |

---

## Mandatory Invariants Checklist

- [ ] **Subprocess Sandbox Default**: External plugin operates in subprocess isolation with Rule 14 pipe drainage.
- [ ] **Qualified Ref Enforcement**: Tool calls require `@<snapshot_id>:e<N>` refs; bare refs are rejected.
- [ ] **2D Disposition Evaluation**: Outcomes report `delivery_disposition` and `retry_disposition`.
- [ ] **IoC Service Key Registration**: Service registers via `AGENT_DESKTOP_KEY` in `ServiceContext`.
