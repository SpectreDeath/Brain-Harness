# CARD: brain-artifact-miner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: brain-artifact-miner                                                 │
│ Category: Agent Orchestration                                               │
│ Version: 1.0.0                                                              │
│ Invocation: /brain-artifact-miner                                           │
│ Triggers: "mine brain artifacts", "salvage scratch scripts",                 │
│           "introspect brain workspace", "triage background tasks"           │
│ Requires: "book-to-skill-forge", "conversation-trajectory-miner",           │
│           "epistemic-memory-lifecycle"                                      │
│ Provides: "brain-artifact-miner-engine", "scratch-tool-archaeologist",       │
│           "task-log-triager"                                                │
│ Target: Filesystem-Native Brain Workspace Archaeology & Artifact Mining     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Core Responsibility | Primary Artifact | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Store Discovery & Boundary-Safe Handshake** | UTF-8 Codec & Shell Read Fallback | `brain_manifest.json` | All target directories enumerated via UTF-8-safe reads; zero protection boundary stalls. |
| **2. Dual-Transcript & Artifact Topology Index** | $O(1)$ Binary Index & Dual Linking | `artifact_topology_map.json` | $O(1)$ byte-offset index compiled; truncated steps dereferenced; null-safe metadata parsed. |
| **3. Scratch Tool Archaeology & Task Triage** | AST Classification & Stderr Drainage | `scratch_and_task_catalog.json` | Scripts classified across $\ge 4$ categories; task triage emitted; zero bare `except: continue`. |
| **4. Dual-Lens Cognitive Bifurcation** | Epistemic vs Procedural Partitioning | `epistemic_procedural_spec.json` | Outputs bifurcated into dual-file Knowledge Vault items and executable skill scaffolds. |
| **5. Skill SDLC Validation & Graph Commit** | Craft Validation & Graph Indexing | `skill_validation_report.json` | SkillValidator passes with zero warnings; skill indexed in knowledge graph with FEEDS edges. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. BOUNDARY-RESILIENT SHELL READ FALLBACK                   │
│ - Never stall on IDE system protection boundary denials.    │
│ - Enforce immediate pivot to Get-Content / Get-ChildItem.   │
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

- [ ] **IDE Boundary Resilience**: Always pivot immediately to shell reads on system protection boundary denials (Rule 46).
- [ ] **Binary Byte-Offset Indexing**: Transcripts over 10 MB must use an $O(1)$ byte-offset seek table rather than loading full text into memory (Rule 48).
- [ ] **Dual-Transcript Synchronization**: Detect `is_truncated: true` and dereference to `transcript_full.jsonl` step at matching index (Rule 22).
- [ ] **Defensive Batch Visibility**: Batch scanning loops must log unexpected errors and reraise `NameError`, `TypeError`, `AttributeError` (Rule 32).
- [ ] **JSON Null-Field Fallback**: Sidecar metadata extraction must use `dict.get("key") or []` to guard against explicit JSON `null` (Rule 33).
- [ ] **Dual-Lens Cognitive Bifurcation**: Mining outputs must strictly separate into epistemic Knowledge Vault items and executable skills (Rule 41).
- [ ] **Canonical Dual-File Vault Format**: Knowledge items must use the canonical dual-file directory format (`metadata.json` + `summary.md`, Rule 40).
- [ ] **Domain-Prefixed Script Naming**: Helper script must be named `brain_artifact_miner.py` to prevent `sys.modules` collisions (Rule 57).
- [ ] **UTF-8 Stream Codec Configuration**: Standard streams reconfigured to UTF-8 at module entrypoint (Rule 23, Rule 50).

---

## Related Skills & References

- [conversation-trajectory-miner](../conversation-trajectory-miner/SKILL.md) — Relational SQLite trajectory mining and proactor-safe WAL autopsy.
- [book-to-skill-forge](../book-to-skill-forge/SKILL.md) — Literature-to-skill distillation and visual brief generation.
- [epistemic-memory-lifecycle](../epistemic-memory-lifecycle/SKILL.md) — Bounded 8-state knowledge item promotion and vault retention.
