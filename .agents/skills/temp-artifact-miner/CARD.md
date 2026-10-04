# CARD: temp-artifact-miner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: temp-artifact-miner                                                  │
│ Category: Agent Orchestration                                               │
│ Version: 1.0.0                                                              │
│ Invocation: /temp-artifact-miner                                            │
│ Triggers: "mine temp artifacts", "salvage visual briefs",                   │
│           "triage pytest sandbox", "extract html architecture reviews"      │
│ Requires: "book-to-skill-forge", "brain-artifact-miner",                    │
│           "conversation-trajectory-miner", "epistemic-memory-lifecycle"      │
│ Provides: "temp-artifact-miner-engine", "visual-brief-extractor",           │
│           "sandbox-triager"                                                 │
│ Target: Ephemeral Runtime Store Mining & Visual Architecture Salvage        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Core Responsibility | Primary Artifact | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Ephemeral Store Discovery & Census Handshake** | Non-Modifying Reads & Codec | `temp_manifest.json` | All candidate temp files inventoried via non-blocking reads; zero destructive deletions. |
| **2. Visual Brief & Topology Parsing** | Multi-Pass Extraction & Context Guard | `brief_catalog.json` | Mermaid DAGs and scorecards parsed; 400KB+ Cytoscape topologies bounded. |
| **3. Test Sandbox & Diagnostics Triage** | Bounded Traversal & Stderr Drain | `sandbox_triage_report.json` | Pytest fixtures inspected to depth $\le 3$; noise roots pruned; trailing stderr surfaced. |
| **4. Dual-Lens Cognitive Bifurcation** | Epistemic vs Procedural Partitioning | `epistemic_procedural_spec.json` | Outputs bifurcated into dual-file Knowledge Vault items and salvaged documentation. |
| **5. Skill SDLC Validation & Graph Commit** | Craft Validation & Graph Indexing | `skill_validation_report.json` | SkillValidator passes with zero warnings; skill indexed in knowledge graph. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EPHEMERAL PURGE DEFENSE & NON-MODIFYING READS            │
│ - Never execute blind rm -rf or file deletions in %TEMP%.   │
│ - Tolerate disappearing files gracefully during discovery.  │
├─────────────────────────────────────────────────────────────┤
│ 2. CONTEXT WINDOW ECONOMY & TOPOLOGY BOUNDING               │
│ - Detect 400KB+ Cytoscape/SVG files and bound DOM blobs.    │
│ - Extract structured metadata summaries without blowout.    │
├─────────────────────────────────────────────────────────────┤
│ 3. DUAL-LENS COGNITIVE BIFURCATION                          │
│ - Bifurcate epistemic truth (Knowledge Vault + isnad) from   │
│   procedural execution (executable agent skills + CARD.md). │
└─────────────────────────────────────────────────────────────┘
```

---

## Mandatory Invariants Checklist

- [ ] **Non-Modifying Ephemeral Reads**: Strictly read-only traversal; never delete temporary files, socket markers, or test fixtures (Rule 46).
- [ ] **Heavy Topology Context Bounding**: Large DOM/SVG files over 100 KB must be summarized; never dump raw graph data into prompts (Rule 9, Rule 48).
- [ ] **Bounded Sandbox Traversal**: Subprocess sandbox audits must enforce depth $\le 3$ and prune `.git`, `.venv`, and `node_modules` (Rule 52).
- [ ] **Defensive Batch Visibility**: Batch discovery loops must log unexpected errors at `logger.warning()` and reraise `NameError`, `TypeError`, `AttributeError` (Rule 32).
- [ ] **JSON Null-Field Fallback**: Parsing optional metadata must use `dict.get("key") or []` (Rule 33).
- [ ] **Dual-Lens Cognitive Bifurcation**: Mining outputs must strictly separate into epistemic Knowledge Vault items and procedural skills (Rule 41).
- [ ] **Canonical Dual-File Vault Format**: Knowledge items must use the canonical dual-file directory format (`metadata.json` + `summary.md`, Rule 40).
- [ ] **Domain-Prefixed Script Naming**: Helper script must be named `temp_artifact_miner.py` to prevent `sys.modules` collisions (Rule 57).
- [ ] **UTF-8 Stream Codec Configuration**: Standard streams reconfigured to UTF-8 at module entrypoint (Rule 23, Rule 50).

---

## Related Skills & References

- [brain-artifact-miner](../brain-artifact-miner/SKILL.md) — Filesystem-native workspace archaeology and scratch utility salvage.
- [conversation-trajectory-miner](../conversation-trajectory-miner/SKILL.md) — Relational SQLite trajectory mining and proactor-safe WAL autopsy.
- [book-to-skill-forge](../book-to-skill-forge/SKILL.md) — Literature-to-skill distillation and visual brief generation.
- [epistemic-memory-lifecycle](../epistemic-memory-lifecycle/SKILL.md) — Bounded 8-state knowledge item promotion and vault retention.
