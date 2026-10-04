# Knowledge Item: Antigravity Tri-Store Trinity & Ephemeral Visual Salvage

> **Identifier:** `ki_temp_20261003_01`  
> **Category:** `memory_and_epistemics`  
> **Provenance:** Antigravity Book-to-Skill Forge (`book-to-skill-forge`)  
> **Source Corpus:** `C:\Users\spectre\AppData\Local\Temp\` (%TEMP%)  
> **Isnād Status:** `VERIFIED`

---

## 1. Problem Statement: The Ephemeral Purge Risk

Modern autonomous agent harnesses generate extensive intermediate intellectual assets: visual architecture diagrams, Mermaid DAG workflows, diagnostic evaluation scorecards, dynamic model routing matrices, and isolated test sandboxes.

In the Antigravity architecture, these assets are systematically generated into the operating system temporary directory (`%TEMP%` / `C:\Users\spectre\AppData\Local\Temp\`) per Pillar I of the deep-module craft standards (`%TEMP%\<skill-name>-<timestamp>.html`).

However, temporary storage is inherently **volatile and unversioned**:
1. Operating systems, disk cleanup utilities, and reboot cycles periodically purge `%TEMP%`, permanently destroying hundreds of hours of distilled architectural diagrams and decision matrices.
2. Agents searching for past architecture reviews or test fixture failure patterns suffer from **Ephemeral Purge Amnesia**, unable to reference prior visual deliberations.
3. Reckless automated cleanup routines (`Remove-Item`, `rm -rf`) can accidentally delete active proactor IPC self-pipe sockets or active test sandboxes.

---

## 2. Solution Architecture: The Antigravity Tri-Store Trinity

The Antigravity AI harness ecosystem organizes agent execution memory and intellectual outputs into three orthogonal, mutually reinforcing tiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE ANTIGRAVITY TRI-STORE MINING TRINITY                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Relational Execution Store (conversations/*.db)                          │
│    └── Mined by: conversation-trajectory-miner                              │
│    └── Data: SQLite step payloads, tool calls, model input/output tokens    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Filesystem Workspace Store (brain/<cid>/)                                │
│    └── Mined by: brain-artifact-miner                                       │
│    └── Data: Python scratch scripts, task plans, walkthroughs, task logs    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Ephemeral Runtime Store (%TEMP%)                                         │
│    └── Mined by: temp-artifact-miner                                        │
│    └── Data: 133 HTML visual briefs, Mermaid DAGs, scorecards, sandboxes    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Operational Guidelines & Invariants

1. **Non-Modifying Ephemeral Reads (Rule 46)**:
   The mining engine must never delete or modify files in `%TEMP%`. Traversal is strictly read-only, ensuring that concurrent running tasks and proactor IPC sockets remain undisturbed.
2. **Context Window Protection & Heavy Topology Bounding (Rule 9, Rule 48)**:
   Skill knowledge graph exports (e.g. `skill-graph-*.html`) contain interactive Cytoscape or SVG DOM graphs averaging 406.5 KB each. The miner detects payloads exceeding 100 KB and extracts metadata summaries rather than flooding prompts with raw DOM trees.
3. **Bounded Traversal of Pytest Sandboxes (Rule 52)**:
   Inspection of `pytest-of-spectre/` fixture directories must bound directory depth to $\le 3$ and actively prune `.git`, `.venv`, and `node_modules`.
4. **Dual-Lens Cognitive Bifurcation (Rule 41)**:
   Outputs must bifurcate cleanly into epistemic truths committed to the Knowledge Vault (`.harness/knowledge/`) and procedural salvaging of visual briefs into repository documentation (`docs/architecture/`).

---

## 4. Provenance & Isnād Chain

- **Source Corpus:** `C:\Users\spectre\AppData\Local\Temp\` (133 HTML briefs, 3 pytest sandboxes, 310.72 MB).
- **Visual Brief:** `C:\Users\spectre\AppData\Local\Temp\book-to-skill-forge-temp.html` (SHA-256 verified).
- **Procedural Engine:** `.agents/skills/temp-artifact-miner/scripts/temp_artifact_miner.py`.
