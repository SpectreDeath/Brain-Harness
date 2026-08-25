# 🧠 Skill Summary Card: `webwright_harness`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        webwright_harness                         │
│ Category:    integration_and_io                        │
│ Invocation:  @tool or ServiceKey                       │
│ Version:     1.0.0                                     │
│ Isolation:   subprocess                                │
│ Provides:    "service.webwright_harness"               │
├────────────────────────────────────────────────────────┤
│ Target:      SWE-style trajectory skill synthesis,     │
│              semantic retrieval, Chromium daemon,      │
│              and multimodal trajectory verification.   │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tool Matrix

| Tool | Purpose | Primary Inputs |
|---|---|---|
| `webwright_skill_learn` | Learn reusable Python skill from trajectories | `trajectory_dirs`, `template`, `library_dir` |
| `webwright_skill_retrieve` | Semantic candidate skill ranking | `task`, `k`, `library_dir` |
| `webwright_skill_route_and_execute` | Direct execution or agent fallback | `task`, `start_url`, `library_dir`, `timeout_s` |
| `webwright_browser_session_manage` | Local Chromium daemon control | `action: create\|info\|release`, `port` |
| `webwright_image_qa` | Multimodal VLM QA on web screenshots | `image_path`, `question`, `model` |
| `webwright_self_reflection` | Trajectory verification & critique | `task`, `screenshots_dir`, `action_history` |

---

## 🛡️ Invariants Checklist
- [x] Subprocess isolation for untrusted skill execution
- [x] JSON Schema validation on all input/output payloads
- [x] Chromium process lifecycle safety with graceful PID release
- [x] Parameter slot extraction with strict typing
