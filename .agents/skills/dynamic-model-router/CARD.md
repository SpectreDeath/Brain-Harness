# Skill Summary Card: `dynamic-model-router`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       dynamic-model-router                      │
│ Category:    agent_orchestration / model-routing       │
│ Invocation:  /dynamic-model-router                     │
│ Trigger:     "switch models automatically",            │
│              "dynamic model router",                   │
│              "multi-model fallback",                   │
│              "llm routing table",                      │
│              "resilient model fallback",               │
│              "route prompts by complexity"             │
│ Version:     1.0.0                                     │
│ Provides:    "dynamic_model_routing"                   │
├────────────────────────────────────────────────────────┤
│ Target:      Architect, configure, and operate         │
│              multi-provider dynamic LLM routing with   │
│              sub-5ms classification and failovers.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Dynamic Routing Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Offline Profiling** | Classify prompt complexity via regex & syntax tokens | Complexity Enum | Evaluated in $< 5\text{ ms}$ with zero network calls |
| **2. Matrix Resolution** | Map tier to decoupled primary & fallback pair | ModelConfig Tuple | Validated provider diversity (`primary.prov != fallback.prov`) |
| **3. Timeout Encasement** | Encase provider calls within tight socket timeouts | Timeout Guard Client | Strict $\le 10.0\text{ s}$ timeout client configured |
| **4. Failover Execution** | Trap exceptions and dispatch secondary fallback | Fallback Result & Log | Failover smoothly executed and recovery warning logged |
| **5. Normalization & Log** | Standardize response into unified canonical schema | NormalizedResponse Schema | Zero vendor SDK object leaks and telemetry recorded |

---

## The Three Pillars Cheat Sheet

### 1. Zero-LLM Classification Heuristics (< 5ms)
- **Code Fences**: Check for markdown code markers (` ``` `) to detect code debugging, generation, or refactoring.
- **Reasoning Keywords**: Match high-cognitive intent tokens (`refactor`, `debug`, `algorithm`, `architecture`, `optimize`).
- **Word Count Thresholds**: Partition into `< 80` words (`SIMPLE`), `80–300` words (`MEDIUM`), and `> 300` words or code (`COMPLEX`).
- **Zero Network Cost**: Never invoke an auxiliary LLM to route an LLM prompt.

### 2. Strict 5-10s Timeout Encasement & Decoupled Bridges
- **Socket Timeouts**: Primary calls capped at $\le 10.0\text{ s}$ to prevent silent upstream hangs from blocking users.
- **Provider Decoupling**: Isolate vendor-specific SDKs inside dedicated adapter functions (`_call_openai`, `_call_anthropic`).
- **Provider Diversity Invariant**: Never assign primary and fallback to the same cloud infrastructure provider.

### 3. Transparent Failover & Canonical Schemas
- **Exception Trapping**: Catch rate limits (`429`), timeouts, and outages; trigger fallback immediately.
- **Recovery Warnings**: Emit structured logs recording failing provider, model name, and error reason.
- **Canonical Envelope**: Return `NormalizedResponse(status, complexity_tier, model_used, fallback_used, response)`.

---

## Verification & Quality Checklist

- [ ] **Sub-5ms Latency**: Complexity profiling executes in $< 5\text{ ms}$ with zero network calls.
- [ ] **Provider Diversity**: Primary and fallback models are verified on distinct cloud infrastructures.
- [ ] **Strict Timeout Guard**: Client-side socket timeout explicitly bounded to $\le 10.0\text{ s}$.
- [ ] **Transparent Failover**: Primary failures transparently trigger secondary fallback with warning logs.
- [ ] **Schema Normalization**: Output packaged in typed `NormalizedResponse` schema with zero raw SDK leak.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored with single-pipe ASCII header and linked.
- [ ] **Deep-Module Compliance**: Passes context linters and skill graph indexers with zero warnings.
