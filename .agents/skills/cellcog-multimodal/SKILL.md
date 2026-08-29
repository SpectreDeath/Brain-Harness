---
name: cellcog-multimodal
description: Orchestrate any-to-any multimodal sub-agent delegation via CellCog. Use when generating 3D models (.GLB), cinematic/social video, multi-track audio/music, executive PDF/XLSX documents, interactive HTML dashboards, or citation-backed deep research.
---

# CellCog Multimodal Sub-Agent Delegation

`cellcog-multimodal` is the authoritative execution blueprint for delegating non-code and cross-modality tasks (3D modeling, video generation, audio/music synthesis, executive PDF/slide creation, and multi-source deep research) to CellCog via `plugin.cellcog`.

Every delegation cycle follows a five-stage progression:

```
[1. Task Assessment] → [2. Prompt & Tag Protocol] → [3. The Visual Brief] → [4. Mandatory Checkpoint] → [5. Execution & Verification]
```

See [CARD.md](CARD.md) for the skill summary card, quick-reference template, and completion criteria checklist.
Consult [REFERENCE.md](REFERENCE.md) for copy-paste golden recipes across the top 5 modalities.
Consult `/crafting-skills` for authoring standards and `/epistemic-isnad-audit` for provenance tracking.

---

## 1. Task Assessment & Modality Selection

Evaluate the user's generative request to select the target operating point (`chat_mode`, `chat_tier`):

1. **Modality & Mode Mapping**:
   - `chat_mode="agent"`: Most tasks — 3D model generation (.GLB), video rendering, audio/podcast synthesis, multi-tab Excel financial models, and code.
   - `chat_mode="creative"`: Design-taste work — interactive HTML dashboards, UI wireframes, brand identity kits, presentation slide decks, creative writing.
   - `chat_mode="team"`: Deep multi-source research ONLY — cross-validation, competitive matrices, and citation-backed synthesis.

2. **Quality Tier Selection**:
   - `chat_tier="flash"`: Default fast/economical tier for light asset generation, quick scripts, or preliminary drafts.
   - `chat_tier="core"`: Balanced tier for standard decks, spreadsheets, and illustrations.
   - `chat_tier="max"`: Maximum depth tier for production video rendering, 3D character rigging, complex data analysis, or legal drafting.

> **Completion criterion**: Target modality identified, `chat_mode` and `chat_tier` selected with rationale.

---

## 2. Prompt Construction & Tag Protocol

Construct the delegation prompt using the dual tag protocol:

1. **Input Grounding (`<SHOW_FILE>`)**:
   - Wrap reference files (PDFs, images, code files, CSV data, audio) in `<SHOW_FILE>/absolute/path</SHOW_FILE>` tags.
   - *Security Invariant*: Never wrap credentials, `.env`, `.git`, or private keys in `<SHOW_FILE>` tags.

2. **Deterministic Output Path (`<GENERATE_FILE>`)**:
   - Wrap desired output file paths in `<GENERATE_FILE>/workspace/output/artifact.ext</GENERATE_FILE>` tags.
   - This guarantees artifacts download directly to deterministic locations rather than ephemeral temp folders.

3. **Explicit Artifact Declarations**:
   - State exact file formats and deliverable types explicitly (e.g. "Create an interactive HTML dashboard, a 60s summary video, and a formatted PDF").

> **Completion criterion**: Prompt assembled with verified absolute `<SHOW_FILE>` inputs and `<GENERATE_FILE>` output destinations.

---

## 3. The Visual Brief

For non-trivial multimodal pipelines, generate an interactive visual summary:

1. **Location**: Write to `%TEMP%\cellcog-delegation-<timestamp>.html` (Windows) or `/tmp/cellcog-delegation-<timestamp>.html` (Unix).
2. **Topology Diagram**: Render a Mermaid graph displaying:
   - Input files (`<SHOW_FILE>`) $\rightarrow$ CellCog Cloud Sub-Agent (`chat_mode` + `chat_tier`) $\rightarrow$ Output Artifacts (`<GENERATE_FILE>`).
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

> **Completion criterion**: Visual brief written to `%TEMP%` and presented to user.

---

## 4. Mandatory Checkpoint

Before dispatching expensive cloud sub-agent tasks, present the delegation plan:

1. Create or update `implementation_plan.md` artifact detailing:
   - Target modality and deliverables list.
   - Selected `chat_mode` and `chat_tier`.
   - List of attached reference files and target output paths.
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user review and approval before executing the API call.

> **Completion criterion**: Explicit user approval received for sub-agent execution.

---

## 5. Execution & Verification

Dispatch the task through the typed `plugin.cellcog` tools:

1. **Invoke Plugin Entrypoint**:
   - For general tasks: Call `cellcog_run(prompt=..., chat_mode=..., chat_tier=...)`.
   - For deep research: Call `cellcog_research(topic=..., attachments=..., chat_tier=...)`.
2. **Artifact Verification**:
   - Confirm downloaded files exist at the specified `<GENERATE_FILE>` paths.
   - Verify file sizes and non-empty content.
3. **Record in Walkthrough**:
   - Update `walkthrough.md` with generated artifact paths and executive summary.

> **Completion criterion**: All requested deliverables verified on disk and recorded in walkthrough.

---

## Anti-Patterns

- **Modality Over-Specification** — Searching for 39 separate tools when `cellcog_run` with an explicit prompt and `chat_mode` handles all modalities seamlessly.
- **Credential Exposure** — Wrapping `.env` files, SSH keys, or secrets inside `<SHOW_FILE>` tags.
- **Tier Waste** — Defaulting to `max` tier for simple icon or text generation that `flash` handles instantly.
- **Missing Output Tags** — Omitting `<GENERATE_FILE>` tags, resulting in downloaded files scattered across default cache folders.
- **Unbounded Delegation** — Dispatching long-running cloud tasks without presenting the `implementation_plan.md` checkpoint.
