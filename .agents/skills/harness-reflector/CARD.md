```
╔══════════════════════════════════════════════════════════════════════╗
║ SKILL:     harness-reflector                                         ║
║ CATEGORY:  memory / epistemics / metacognition                       ║
║ INVOCATION:/harness-reflector or harness reflect                     ║
║ TRIGGERS:  reflect on past work, learn from internal reports,        ║
║            distill heuristics from past cycles, self-reflection      ║
║ TARGET:    %TEMP% HTML reports, transcript logs, walkthroughs        ║
╚══════════════════════════════════════════════════════════════════════╝
```

# Harness Reflector — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Completion Gate |
|---|---|---|
| **1. Harvest** | Discover and parse `%TEMP%` HTML reports and conversation transcripts | Reports and transcripts indexed with timestamps & friction tokens |
| **2. Distill** | Run 4-axis cross-correlation to synthesize invariants and anti-patterns | Candidate heuristics formulated with confidence ratings |
| **3. Visual Brief** | Render interactive HTML brief with Mermaid lineage DAG in `%TEMP%` | Report generated and absolute clickable file link surfaced |
| **4. Checkpoint** | Present candidate Knowledge Items for human-in-the-loop review | Explicit approval gate (`RequestFeedback: true`) recorded |
| **5. Vault Commit** | Persist verified KIs to `storage.knowledge_vault` and `.harness/knowledge/` | Knowledge items saved, on-disk files written, isnad verified |

---

## Vocabulary & Levers

- **Endogenous Memory**: Internal developmental history, execution trajectories, and historical artifacts produced by the Harness itself.
- **Visual Brief**: Self-contained interactive HTML review report written to `%TEMP%` with Mermaid diagrams and dark styling.
- **Isnad Lineage**: Verifiable chain-of-custody linking an architectural claim back to its exact primary source (HTML report, log line, commit SHA).
- **Knowledge Vault**: Ground-truth storage engine (`storage.knowledge_vault`) maintaining persistent, queryable `KnowledgeItemRecord` entities.
- **Episodic Triangulation**: Cross-referencing user intent, tool traces, runtime errors, and code diffs to deduce root causes and durable heuristics.

---

## Mandatory Invariants Checklist

- [ ] Every distilled Knowledge Item must cite at least one empirical primary source artifact in `isnad.claims`.
- [ ] No speculative or hypothetical assertions may be marked with status `VERIFIED` without transcript/report evidence.
- [ ] The Visual Reflection Brief must be generated in `%TEMP%` and linked before committing to persistent storage.
- [ ] The Mandatory Checkpoint gate must be observed before modifying `.harness/knowledge/` or repo rules.
- [ ] All exported on-disk knowledge items must follow the canonical dual-file directory standard (`metadata.json` + markdown summary).
