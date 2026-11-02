```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: agent-reach-browser-bridge                                    │
│ Category: integration_and_io / web-scraping                          │
│ Version: 1.0.0                                                       │
│ Invocation: /agent-reach-browser-bridge                              │
│ Triggers: "agent reach", "reach read", "cloak browser", "cdp web",    │
│           "walled garden scraping", "web extraction", "opencli"      │
│ Requires: "agent_reach", "integration_and_io"                        │
│ Target: Multi-channel web extraction, CDP browser & session bridge   │
└──────────────────────────────────────────────────────────────────────┘
```

# Agent Reach Browser Bridge — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Channel Discovery** | Match URL or action to registered channel | `ReachChannelDescriptor` | Target platform mapped or public web fallback |
| **Stage 2: Fallback Cascade** | Execute ordered backends (API -> Browser -> Native) | `ReachActionQuery` | First successful backend returns payload |
| **Stage 3: Credential Scrubbing** | Redact auth tokens & user:pass credentials | Sanitized payload | Clean text stream without auth leak |
| **Stage 4: Envelope Gate** | Wrap in Schema v1 envelope with error taxonomy | `ReachEnvelope` | Valid envelope with `FINAL_CODES` classification |

---

## Vocabulary & Levers

- **Schema v1 Envelope**: Standardized `{schema_version, ok, channel, action, backend, items, meta, error}` return format.
- **`FINAL_CODES`**: Immutable set of non-retryable errors (`NEED_LOGIN`, `RATE_LIMITED`, `PLATFORM_BLOCKED`, `NOT_FOUND`, `BAD_INPUT`).
- **CloakBrowser**: Anti-fingerprinting browser engine running over localhost CDP (`127.0.0.1`) with 600s idle auto-reclamation.
- **Private Session Sandbox**: Tool-specific `$HOME` redirection (`~/.agent-reach/sessions/<tool>/`) with symlink boundary enforcement.
- **Slotted/Frozen Dataclasses (Rule 12)**: High-efficiency immutable structures for query, action, and envelope entities.

---

## Mandatory Invariants Checklist

- [ ] **Unified JSON Envelope**: Every extraction call must emit a Schema v1 envelope; never return bare HTML or unstructured stdout.
- [ ] **Strict Final Error Honor**: Never attempt backend fallbacks or retry loops on `FINAL_CODES` errors.
- [ ] **Loopback Only CDP**: Browser automation must strictly bind to `127.0.0.1` and never route DevTools traffic through external proxies.
- [ ] **Private Session HOME**: Third-party CLI tools must execute with `$HOME` redirected to private session directories.
- [ ] **Subprocess Pipe Drainage**: All asynchronous subprocess transports must explicitly close standard pipes in `finally` blocks (Rule 14).

