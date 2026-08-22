---
name: mind-reader
description: Reflect on, introspect, and extract foundational learnings from an attached brain, external IDE history, or foreign knowledge library. Use when the user asks to read a brain, introspect agent history, learn from past trajectories, distill knowledge from another harness, or run the mind reader reflection loop.
---

# Mind Reader: Cognitive Introspection & Knowledge Distillation Engine

`mind-reader` is the reflective introspection engine for Brain Harness. Operating atop `plugin.brain_bridge`, it attaches to foreign agent brains, IDE session records, and knowledge vaults to analyze past architectural decisions, error recovery trajectories, and implicit heuristics—distilling them into actionable, grounded Knowledge Items (KIs).

Every mind reading reflection session follows a five-stage progression:

```
[1. Attach & Detect] → [2. 4-Axis Introspection] → [3. Visual Insight Brief] → [4. Synthesis Checkpoint] → [5. KI Extraction & Lineage Commit]
```

See [CARD.md](CARD.md) for the companion summary card, 4-axis prompt matrix, and invariants.
Consult `/crafting-skills` for authoring standards and `/epistemic-isnad-audit` for chain-of-custody lineage rules.

---

## 1. Attach & Format Detection

Mount the target brain folder using the `plugin.brain_bridge` entrypoint:

1. **Invoke `brain_attach`**:
   - `folder_path`: Target folder path provided by the user.
   - `alias`: Descriptive mnemonic identifier (e.g., `source_brain`, `antigravity_archive`).
   - `read_transcripts`: `true` to ingest execution steps, tool invocations, and error recoveries.
   - `attach_mode`: `"lens"` (read-only ephemeral introspection).
2. **Verify Format Signature**:
   Confirm whether the detected signature is `antigravity_brain`, `harness_instance`, `ide_memo`, `obsidian_vault`, `git_repository`, or `raw_docs`. (For in-depth Git repository code and commit trajectory distillation, see `/repo-reader`).
3. **Log Mount Volume**:
   Confirm chunk count, transcript count, and unique vocabulary index size.

> **Completion criterion**: Target brain mounted with `status: "ok"` and signature classified.

---

## 2. 4-Axis Introspection Matrix

Execute four structured queries via `brain_query` across the mounted brain to cover the full cognitive surface:

```
┌─────────────────────────────────────────────────────────────┐
│                   4-AXIS INTROSPECTION                      │
├──────────────────────────────┬──────────────────────────────┤
│ Axis 1: Architectural Logic  │ Axis 2: Error Trajectories   │
│ - Design invariants          │ - Failed commands / tests    │
│ - Seam choices & trade-offs  │ - Recovery paths chosen      │
├──────────────────────────────┼──────────────────────────────┤
│ Axis 3: Epistemic Habits     │ Axis 4: Delta Learnings      │
│ - Common tools / workflows   │ - Novel strategies           │
│ - Verification standards     │ - Contradictions to priors   │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Axis 1 (Architectural Logic)**:
   - Query: `"Why was this architecture, service key, or module design chosen? What trade-offs were made?"`
   - Purpose: Surface design intent and rationale.
2. **Axis 2 (Error Trajectories & Recoveries)**:
   - Query: `"What commands, tests, or approaches failed and how were they debugged or corrected?"`
   - Purpose: Learn from prior friction and avoid repeating dead ends.
3. **Axis 3 (Epistemic Habits & Conventions)**:
   - Query: `"What verification standards, test markings, or coding guidelines were consistently applied?"`
   - Purpose: Understand procedural norms.
4. **Axis 4 (Delta Learnings & Surprises)**:
   - Query: `"What techniques or insights are unique, unexpected, or counter-intuitive?"`
   - Purpose: Extract novel knowledge.

> **Completion criterion**: 4 query result sets harvested, sorted by cosine relevance score, with source line pointers.

---

## 3. The Visual Insight Brief

Synthesize the harvested insights into a self-contained, interactive HTML report:

1. **Output Location**: Write to `%TEMP%\mind-reader-<timestamp>.html` (Windows) or `/tmp/mind-reader-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Use Tailwind CSS and Mermaid.js via CDN in dark mode (`#0d1117`).
   - Include a Mermaid **Cognitive Topology DAG** mapping identified problem areas $\rightarrow$ attempted strategies $\rightarrow$ final distilled solutions.
   - Display a side-by-side comparison of **Prior Assumptions vs. Distilled Brain Learnings**.
3. **Delivery**: Surface the absolute file path with clickable links to the user.

```html
<!-- Location: %TEMP%\mind-reader-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mind Reader: Cognitive Introspection Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Mind Reader Introspection Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Cross-Brain Cognitive Distillation & Trajectory Analysis</p>
  </header>
  <!-- Mermaid DAG & 4-Axis Analysis Grid -->
</body>
</html>
```

> **Completion criterion**: Standalone HTML brief generated in `%TEMP%` and delivered to user.

---

## 4. Synthesis Checkpoint

Present the candidate learnings to the user before committing any state:

1. Formulate atomic candidate Knowledge Items (KIs) with:
   - **Title**: Actionable heuristic or architecture pattern.
   - **Context**: Problem space and trigger conditions.
   - **Distilled Learning**: Positive recommendation and mitigation strategy.
   - **Provenance Link**: Path and line number in the source brain.
2. Set `RequestFeedback: true` in the plan / modal checkpoint.
3. Pause for user feedback on which items to retain or adjust.

> **Completion criterion**: User review checkpoint completed; approved items selected for commit.

---

## 5. KI Extraction & Lineage Commit

Persist approved learnings into the host repository's knowledge directory:

1. **Target Directory**: Write to `.harness/knowledge/<ki_id>/` or `.context/` on the host.
2. **Metadata Schema (`metadata.json`)**:
   ```json
   {
     "id": "ki_20260821_01",
     "title": "Subprocess Plugin Sandbox Boundary Guard",
     "source_target": "C:/Users/.../brain",
     "detected_format": "antigravity_brain",
     "isnad": {
       "decision_id": "dec_20260821_01",
       "claims": [
         {
           "assertion": "Untrusted plugins run in subprocess sandboxes",
           "lineage": [
             {"node_type": "primary_code", "uri": "transcript.jsonl#L142", "verified": true}
           ]
         }
       ],
       "status": "VERIFIED"
     },
     "tags": ["plugin_system", "sandbox", "isolation"]
   }
   ```
3. **Artifact Summary**: Co-locate `summary.md` detailing the operational guideline.

> **Completion criterion**: Approved KIs written with unbroken Isnad provenance links.

---

## Anti-Patterns

- **Passive Ingestion** — Mounting a brain without interrogating error recovery trajectories (Axes 2 & 4).
- **Unanchored KI Commits** — Writing learned items without exact file and transcript line citations.
- **Foreign Brain Mutation** — Writing modified state back into an external target directory rather than preserving read-only isolation.
- **Surface Scraping** — Only reading file headers without querying conversational reasoning steps.
