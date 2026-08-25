# 🧠 Skill Summary Card: `stagehand_browser`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        stagehand_browser                         │
│ Category:    integration_and_io                        │
│ Invocation:  @tool or ServiceKey                       │
│ Version:     1.0.0                                     │
│ Isolation:   subprocess                                │
│ Provides:    "service.stagehand_browser"               │
├────────────────────────────────────────────────────────┤
│ Target:      Next-Gen AI browser automation protocol:  │
│              NL Act, Schema Extract, DOM Observe,      │
│              and WebMCP tool discovery & invocation.   │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tool Matrix

| Tool | Purpose | Primary Inputs |
|---|---|---|
| `stagehand_act` | Execute NL browser action | `action`, `model`, `timeout_s`, `variables` |
| `stagehand_extract` | Schema-driven DOM extraction | `instruction`, `schema`, `model`, `use_text_extract` |
| `stagehand_observe` | DOM discovery & action suggestions | `instruction`, `model`, `return_action` |
| `stagehand_webmcp_tool_invoke` | WebMCP protocol discovery/invocation | `tool_name`, `arguments`, `page_id` |
| `stagehand_session_control` | Browser session lifecycle & evaluate | `action: init\|goto\|screenshot\|evaluate\|close`, `url` |

---

## 🛡️ Invariants Checklist
- [x] Subprocess isolation for CDP & Playwright sessions
- [x] Strict parameter JSON schemas for all tool calls
- [x] WebMCP tool enumeration and execution compatibility
- [x] Graceful session teardown and error handling
