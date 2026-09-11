# Skill Summary Card: `ai-file-analysis-agent`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       ai-file-analysis-agent                    │
│ SKILL:        ai-file-analysis-agent                    │
│ Category:    integration_and_io / file_analysis        │
│ Invocation:  /ai-file-analysis-agent                   │
│ Triggers:    "build file analysis agent",              │
│              "analyze document with AI",               │
│              "RAG vs direct upload",                   │
│              "document question answering agent"       │
│ Version:     1.0.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.ai_file_analysis_agent"          │
├────────────────────────────────────────────────────────┤
│ Target:      Design, configure, ground, and verify     │
│              document-analyzing AI agents with Direct  │
│              File API and negative constraint prompts. │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Agent Lifecycle Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Pre-flight Ingestion & Validation** | Verify existence, extension whitelist, and size bounds | `FileValidationResult` | `Input file existence and extension whitelist verified` |
| **2. Context Architecture Triage** | Select Direct File API vs Chunked Vector RAG pipeline | Architecture Route & Config | `Direct API vs RAG pipeline routing selected` |
| **3. Grounded Prompt Assembly** | Inject 10 negative grounding constraints and role profile | Grounded System Prompt | `10 negative grounding constraints assembled` |
| **4. Conversational Loop & Fault Shielding** | Implement conversational turn loop with error handling | Interactive / CLI Runner | `Turn loop handles empty inputs and API errors` |
| **5. Security Hardening & PII Quarantine** | Isolate env credentials and defend against document injection | Hardened Security Policy | `Zero hardcoded secrets and prompt injection shielded` |

---

## Authoritative Tooling Seams

```bash
# 1. Pre-flight file validation (existence, extension whitelist, size)
python scripts/file_agent_cli.py validate-file <path> [--json]

# 2. Assemble 10 grounding rules with specialized role addendum
python scripts/file_agent_cli.py assemble-prompt [--role research|legal|resume|tabular] [--json]

# 3. Offline staged dry-run of request payload
python scripts/file_agent_cli.py dry-run --file <path> --question "<query>" [--role <role>]

# 4. Audit model response against grounding constraints
python scripts/file_agent_cli.py audit-response --text "<output>" [--file <path>] [--json]
```

---

## Deep Reference Blueprints

- [`direct-api-vs-rag-guide.md`](references/direct-api-vs-rag-guide.md) — Latency, token budget, and complexity trade-offs between Direct API vs RAG.
- [`grounding-and-role-catalog.md`](references/grounding-and-role-catalog.md) — The 10 Negative Grounding Constraints and 4 Specialized Role Profiles.

---

## Tri-Pillar Architecture Cheat Sheet

### 1. The Pre-flight Boundary
Never pass unvalidated user paths directly to API clients. Whitelist extensions (`.pdf`, `.docx`, `.csv`, `.txt`), verify existence, and measure payload size before dispatch.

### 2. Negative Grounding Invariants
Hallucinations are minimized through explicit negative boundaries: direct answers, explicit inference tagging, and explicit refusal when context is insufficient.

### 3. Fault-Tolerant Session Execution
Wrap API dispatches inside structured exception handlers, sanitize empty/whitespace turns, and quarantine unverified document content from instruction hierarchy.

---

## Mandatory Invariants Checklist

- [ ] **Extension Whitelist Enforcement**: Only allow `.pdf`, `.docx`, `.csv`, and `.txt` files; reject all others pre-flight.
- [ ] **Context Routing Triage**: Route files $\le 50$ MB to Direct File API; route large corpora to chunked vector RAG.
- [ ] **10 Grounding Constraints**: Inject all 10 negative grounding constraints into system prompt to eliminate hallucinations.
- [ ] **Direct Answer Economy**: Respond directly to the user's specific query without conversational filler or preambles.
- [ ] **Inference Flagging**: Explicitly prefix any logical deductions beyond literal document text with `[INFERENCE]`.
- [ ] **Secret Isolation**: Load API credentials exclusively via environment variables (`OPENAI_API_KEY`); never hardcode.
