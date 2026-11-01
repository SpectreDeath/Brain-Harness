```
┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: context-type-system                                             │
├────────────────────────────────────────────────────────────────────────┤
│ Title       : Context Type System & Semantic Provenance Ledger         │
│ Cluster     : memory_and_epistemics                                    │
│ Service Key : service.context_type_system                              │
│ CLI Seam    : harness context add | transform | validate-tool | ledger │
│ Invariants  : Rule 11, Rule 12, Rule 16, Rule 37, Rule 44, Rule 47     │
└────────────────────────────────────────────────────────────────────────┘
```

# Context Type System — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Channel Ingestion** | Ingest content into instruction, memory, evidence, or tool_output | `context_item.json` | Item registered with immutable origin ID |
| **2. Tool Validation** | Validate tool results and elevate to evidence | `evidence_item.json` | Validation passes and new evidence ID issued |
| **3. Budget Allocation** | Allocate token quotas and assemble prompt | `assembled_prompt.txt` | Total tokens bounded strictly $\le$ quota |
| **4. Provenance Audit** | Audit provenance ledger and trace derivation chains | `isnad_lineage.json` | Full multi-hop derivation lineage verified |

---

## Mandatory Invariants Checklist

- [ ] **Channel Isolation Invariant**: Raw `tool_output` must never transition directly to `instruction`.
- [ ] **Tool Validation Invariant**: Promotion of `tool_output` to `evidence` requires `validate_tool_output` validation.
- [ ] **Token Ceiling Invariant**: Context prompts must respect configured token budgets and channel quotas.
- [ ] **Provenance Chain Invariant**: All item transformations must record origin lineage in the provenance ledger.
