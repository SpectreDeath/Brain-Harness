---
name: agent-reach-browser-bridge
description: Scaffold, configure, and format multi-platform channel routing, credential scrubbing, and unified Schema v1 result envelopes for AI agents. Envelope formatting only. Do not use for generic SQL querying or raw binary network sniffing.
---

# Agent Reach Browser Bridge: Architecture & Integration

The `agent-reach-browser-bridge` skill provides structured domain capabilities for orchestrating multi-platform web extraction, walled-garden content retrieval (YouTube, GitHub, Reddit, Twitter, Bilibili, Xiaohongshu, Boss直聘, V2EX), dedicated anti-fingerprint CloakBrowser sessions over Chrome DevTools Protocol (CDP), and normalized Schema v1 result envelopes for autonomous AI coding agents.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The Three Foundational Pillars

### 1. Unified Schema v1 Result Envelope & Error Taxonomy
Standardizing all scraping and extraction outputs into an immutable `{schema_version, ok, channel, action, backend, items, meta, error}` JSON envelope. Categorizes failures into deterministic final codes (`FINAL_CODES`: `NEED_LOGIN`, `RATE_LIMITED`, `PLATFORM_BLOCKED`, `NOT_FOUND`, `BAD_INPUT`) versus transient retryable codes (`TIMEOUT`, `UPSTREAM_BROKEN`, `NEED_SETUP`), allowing agent reasoning loops to branch reliably without brittle DOM parsing.

### 2. Deterministic Multi-Tier Backend Fallback Cascades
Decoupling user actions from fragile single-scraper implementations through ordered backend cascades:
- **Tier 1 (Public Web API)**: Zero-credential low-latency JSON endpoints.
- **Tier 2 (Stealth Browser)**: Local CloakBrowser automation over loopback CDP (`127.0.0.1`).
- **Tier 3 (Native Tool / CLI)**: Authenticated third-party command-line utilities.
Applies adaptive circuit breaking (`BACKEND_PAUSE_SECONDS`) to pause failing backends and prevent agent compute thrashing.

### 3. Non-Invasive Session Sandboxing & Credential Redaction
Enforcing strict filesystem isolation by redirecting third-party CLI `HOME` and `USERPROFILE` environments into private per-tool directories (`~/.agent-reach/sessions/<tool>/`). Validates symlink safety and automatically scrubs inline HTTP basic auth credentials (`scrub_url_credentials`) before surfacing outputs to the agent context.

---

## Operational Workflow

```
[Agent Tool Request] ──► [URL / Channel Matcher (can_handle)]
                                   │
                                   ▼
                   [Layered Backend Fallback Cascade]
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
          [1. Public API]   [2. CloakBrowser]  [3. Native CLI]
          (Zero-Auth REST)   (CDP 127.0.0.1)   (Private $HOME)
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                      [Credential Scrubber Engine]
                                   │
                                   ▼
                   [Unified Schema v1 JSON Envelope]
```

---

## Anti-Patterns

- **Raw HTML Extraction Output** — Returning unparsed HTML or noisy terminal stdout directly to LLM context instead of Schema v1 JSON envelopes.
- **Host User Home Contamination** — Allowing third-party scraping utilities to dump login cookies into the default `$HOME` instead of private sandboxes.
- **Unbounded Throttled Retries** — Continuing to retry rate-limited or login-gated endpoints without honoring `FINAL_CODES` circuit breakers.
- **Zombie Browser Leaks** — Failing to shut down idle browser processes after completion, resulting in stranded Chromium handles.
- **Plaintext Credential Leakage** — Permitting user:password secrets in URLs to pass unscrubbed into model trajectories.

