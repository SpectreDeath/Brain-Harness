# Skill Summary Card: `ai-native-harness-engineer`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       ai-native-harness-engineer                │
│ Category:    agent_orchestration / harness_engineering │
│ Invocation:  /ai-native-harness-engineer               │
│ Trigger:     "harness engineering",                    │
│              "make company ai native",                 │
│              "build coding gates",                     │
│              "credential-free mcp",                    │
│              "stop trusting the ai",                   │
│              "track documentation drift"               │
│ Version:     1.0.0                                     │
│ Provides:    "ai_native_harness_engineering"           │
├────────────────────────────────────────────────────────┤
│ Target:      Architect, construct, and govern          │
│              production AI coding harnesses using      │
│              4 behavioral gates and zero-cred MCP.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Harness Engineering Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Scoping & Telemetry** | Pick annoying workflow, structure data, set drift baseline | Process Scope & Baseline | Bounded process isolated & drift formula defined |
| **2. Rules & Graveyard** | Author AGENTS.md, tech recipes, and rejected ideas list | Repository Rules File | Architecture bounded & rejected patterns cataloged |
| **3. Four Behavioral Gates** | Wire typecheck, 100% coverage, e2e simulation, live demo | 4-Gate Behavioral Pipeline | 100% logic coverage enforced & demo page authored |
| **4. Credential-Free MCP** | Deploy MCP forwarding user PATs with dynamic RBAC | Zero-Credential MCP Server | Server holds 0 creds & audit log records user name |
| **5. Drift & Mining** | CI code-to-doc alerts, negative gap mining, SME gates | Drift Telemetry Engine | Unanswered queries ranked into authoring backlog |

---

## The Three Pillars Cheat Sheet

### 1. The Four Behavioral Verification Gates
- **Gate 1 (Typecheck)**: `tsc --noEmit` / `mypy` — 0 type errors across entire repo.
- **Gate 2 (100% Logic Coverage)**: Non-negotiable branch/function coverage on business logic.
- **Gate 3 (E2E User Simulation)**: Playwright plain-English assertions of visible user behavior.
- **Gate 4 (Live App Verification)**: Live boot check + agent-authored runnable usage demonstration page.
- *Spend gate budget on behavior, not syntax linters.*

### 2. Zero-Credential Enterprise MCP Architecture
- **Zero DB Access**: MCP server holds 0 credentials and no direct DB connection.
- **User PAT Passthrough**: Forwards user personal access token with every request.
- **Dynamic RBAC**: API enforces user's live role on every call; instant permission revocation.
- **Uniform Error Defense**: Clean 403 error payloads (`isError: true`); identical 404 responses for non-existent and hidden resources to prevent enumeration.

### 3. Continuous Drift Telemetry & Negative Backlog Mining
- **Code-to-Doc Drift**: CI detects code changes matching doc paths; shifts approval badge to amber.
- **Negative Query Logging**: Unanswered assistant questions become a demand-ranked authoring backlog.
- **Human Authority Gates**: Inline `[!VERIFY]` for uncertainty, `[!SME]` for compliance locks.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Instructions define direct target actions and concrete engineering constraints.
- [ ] **Domain Vocabulary**: Employs rigorous domain concepts (*harness*, *trust inversion*, *credential-free MCP*, *drift count*, *payload omission*, *negative query backlog*).
- [ ] **Exhaustive Completion Criteria**: Every stage specifies unambiguous verification gates.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored with single-pipe `│` borders and `SKILL:` tag.
- [ ] **Zero-Fork Configuration**: Co-located `config.default.yaml` defining baseline operational budgets.
- [ ] **Pre-Flight Validation**: Passes `python -m harness.cli skills validate` with zero warnings.
