# CARD: conversation-trajectory-miner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: conversation-trajectory-miner                                        │
│ Category: Agent Orchestration                                               │
│ Version: 1.0.0                                                              │
│ Invocation: /conversation-trajectory-miner                                  │
│ Triggers: "conversation mining", "trajectory archaeology",                  │
│           "friction analysis", "sqlite wal autopsy"                         │
│ Requires: "book-to-skill-forge", "epistemic-memory-lifecycle"               │
│ Provides: "trajectory-mining-engine", "sqlite-wal-scanner"                  │
│ Target: Multi-Store Autobiographical Trajectory Mining & Skill Synthesis    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Core Responsibility | Primary Artifact | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Store Handshake & Relational Autopsy** | Read-Only Proactor Handshake | `trajectory_manifest.json` | Read-only connection established via `?mode=ro`; schema verified with zero locks. |
| **2. Byte-Offset Seam Unpacking & Lazy Indexing** | $O(1)$ Binary Indexing | `byte_offset_index.json` | Byte-offset index compiled; sub-millisecond seek retrieval verified without memory blowout. |
| **3. Friction Archaeology & Step Analysis** | Failure Cluster Isolation | `friction_diagnostic_report.json` | Step distribution quantified; retry loops and errors isolated into prioritized scorecard. |
| **4. Dual-Lens Cognitive Bifurcation** | Epistemic vs Procedural Partitioning | `epistemic_procedural_spec.json` | Output strictly bifurcated into Knowledge Vault items and executable skill scaffolds. |
| **5. Skill SDLC Validation & Graph Commit** | Craft Validation & Graph Indexing | `skill_validation_report.json` | SkillValidator passes with zero warnings; skill indexed in knowledge graph with FEEDS edges. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PROACTOR-SAFE READ-ONLY HANDSHAKE                        │
│ - Never connect to active SQLite WAL databases in RW mode.  │
│ - Enforce sqlite3.connect("file:<path>?mode=ro", uri=True). │
├─────────────────────────────────────────────────────────────┤
│ 2. O(1) BINARY BYTE-OFFSET SEEK TABLES                      │
│ - Never load multi-megabyte JSONL / logs via f.readlines(). │
│ - Build offset lookup tables scanned once in binary mode.   │
├─────────────────────────────────────────────────────────────┤
│ 3. DUAL-LENS COGNITIVE BIFURCATION                          │
│ - Bifurcate epistemic truth (Knowledge Vault + isnad) from   │
│   procedural execution (executable agent skills + CARD.md). │
└─────────────────────────────────────────────────────────────┘
```

---

## Mandatory Invariants Checklist

- [ ] **Proactor-Safe Read-Only Handshake**: All SQLite databases must be connected using URI read-only mode (`?mode=ro`) to prevent lock contention with live IDE workers.
- [ ] **Binary Byte-Offset Indexing**: Sequential transcript reads over 10 MB must use an $O(1)$ byte-offset seek table rather than loading full text into memory.
- [ ] **Dual-Lens Cognitive Bifurcation**: Mining outputs must strictly separate into epistemic Knowledge Vault items (`.harness/knowledge/`) and executable skills (`.agents/skills/`).
- [ ] **Lossy Protobuf Resilience**: Unrecognized protobuf payloads must be handled via UTF-8 lossy decoding and `executor_metadata` relational fallbacks.
- [ ] **Canonical Dual-File Vault Format**: Knowledge items must use the canonical dual-file directory format (`metadata.json` + `summary.md`).
- [ ] **UTF-8 Stream Codec Configuration**: All python CLI runners and entrypoints must configure standard output/error to UTF-8.
