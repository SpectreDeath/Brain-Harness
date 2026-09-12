```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        agentwikis-router                        │
│ Category:     knowledge_and_skills                     │
│ Invocation:   /agentwikis-router                       │
│ Triggers:     "agentwikis", "wiki scope", "match skill"│
│               "for-agents", "llms.txt", "agent wiki"   │
│ Version:      1.1.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.agentwikis_router"              │
├────────────────────────────────────────────────────────┤
│ Target:       Route developer tasks against AgentWikis │
│               knowledge bases, verify scope, and       │
│               dispatch local or curated skills.        │
└────────────────────────────────────────────────────────┘
```

# AgentWikis Router — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **1. Scope & Trust Triage** | Parse query keywords, compute match scores across 62 wikis & 25 skills, calibrate abstention | `match.json` | `Scope verified and confidence calibrated` |
| **2. Contracted Medallion Pipeline** | Validate corpus against Open Data Contract (ODCS) across Bronze, Silver, Gold tiers | `contract_report.json` | `Open Data Contract validated` |
| **3. Visual Brief & Topology Review** | Render hybrid data topology DAG and blast radius table to HTML brief | `agentwikis_routing_brief.html` | `Visual Brief rendered` |
| **4. 6-Dimension Quality Gating** | Profile corpus across Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness | `quality_scorecard.md` | `Quality score >= 85.0%` |
| **5. Slice Retrieval & Dispatch** | Extract targeted Markdown sections locally from `llms-full.txt`, dispatch skills, cite provenance | `doc_slice.md` | `Documentation slice retrieved and dispatched` |

---

## Input & Output Schema Specification

### Input Schema
| Field | Type | Required | Description |
|---|---|---|---|
| `task_query` | string | Yes | The technical question, goal, or problem statement |
| `wiki_slug` | string | Optional | Targeted wiki identifier (e.g. `hermes`, `vllm`, `claude-code`) |
| `category` | string | Optional | Domain category filter (`agents`, `inference`, `devtools`, etc.) |
| `offline_first` | boolean | Optional | Whether to prefer local corpus (default: `true`) |
| `limit` | integer | Optional | Max recommendations to return (default: `3`) |

### Output Schema
| Field | Type | Description |
|---|---|---|
| `in_scope` | boolean | True if task is covered by AgentWikis scope declarations |
| `calibrated_confident` | boolean | Calibrated confidence indicator (~94% correct abstention) |
| `matched_wikis` | list[object] | Ranked wikis with `slug`, `score`, and `scope_covers` |
| `matched_skills` | list[object] | Curated AgentWikis skills matching user intent |
| `document_extracted` | string | Relative path of extracted documentation file |
| `quality_scorecard` | object | DAMA 6-dimension data quality audit metrics |
| `fallback_recommendation`| string | `"none"` if in-scope, or `"web_search"` if out-of-scope |

---

## Mandatory Invariants Checklist

- [ ] **Scope Boundary Invariant**: Answers are strictly bounded by declared `scope.covers`; questions triggering `scope.notCovered` force immediate abstention.
- [ ] **Calibrated Abstention Invariant**: Calibrated confidence `false` forces fallback to web search rather than guessing (~94% correct abstention).
- [ ] **Relocatable Path Invariant**: Script paths resolve dynamically via config, environment, or relative discovery with zero hardcoded paths.
- [ ] **Open Data Contract Compliance**: All corpus entities conform to machine-readable Open Data Contract (ODCS) schema.
- [ ] **Slotted Domain Model Invariant**: Domain models strictly enforce `slots=True, frozen=True` immutability (`Rule 12`).
- [ ] **Zero-Latency Offline Extraction**: In-scope queries extract targeted Markdown sections locally from `llms-full.txt` without remote latency.

---

## Operational Levers & Anti-Patterns

- **Scope Boundary**: Declared domain limits (`covers` vs `notCovered`) enforced to eliminate hallucinations.
- **Calibrated Abstention**: Systematic fallback to web search when `calibrated_confident` is false.
- **Open Data Contract**: Machine-readable specification (`contracts/agentwikis_contract.yaml`) governing corpus schemas.
- **Medallion Lakehouse**: Layered data refinement (Bronze raw, Silver slotted entities, Gold curated agent marts).
- **6-Dimension Quality**: Automated gating across Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness.
- **Offline Cache**: Local 9.77 MB `llms-full.txt` store delivering instant zero-latency retrieval.
- **MCP Bridge**: Compatibility mode interfacing with `agentwikis-mcp` tools.
