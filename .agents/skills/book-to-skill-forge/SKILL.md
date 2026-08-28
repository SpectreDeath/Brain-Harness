---
name: book-to-skill-forge
description: Transform non-fiction books, technical articles, frameworks, and video transcripts into deep-module AI agent skills and interactive coaching rubrics. Use when the user asks to turn a book into a skill, convert an article or lecture into a skill, forge a skill from literature or video transcripts, or operationalize a methodology into an executable agent blueprint.
---

# Book-to-Skill Forge: Literature & Media Synthesis Engine

`book-to-skill-forge` is the cognitive extraction and skill authoring engine that transforms intellectual literature—non-fiction books, methodology manuals, research papers, long-form articles, and video transcripts—into executable, deep-module AI agent skills (`SKILL.md` + `CARD.md`) and interactive coaching rubrics.

Rather than producing passive, forgettable summaries that suffer from the **"Abstraction Problem"**, `book-to-skill-forge` enforces the **Shu-Ha-Ri framework principle**: it extracts concrete operational steps, diagnostic interview questions, strict author rubrics, and explicit anti-pattern defenses into modular, on-demand agent skills indexed in the Harness Skill Knowledge Graph.

Every literature-to-skill forging session executes this five-stage progression:

```
[1. Ingest & Deconstruct] → [2. Framework & Rubric Extraction] → [3. The Visual Forge Brief] → [4. Mandatory Checkpoint Gate] → [5. Skill Graph & Card Commit]
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage reference matrix, and quality checklist.
Consult `/crafting-skills` for skill authoring standards, `/repo-to-plugin-forge` for codebase plugin synthesis, and `/epistemic-isnad-audit` for primary source provenance.

---

## 1. Ingest & Deconstruct

Ingest and modularize the source material into high-density conceptual chunks without context flooding:

1. **Ingest Source Content**:
   - **Books / Long Articles**: Parse EPUB, PDF, Markdown book notes, or Zettelkasten slip-boxes into structured text.
   - **Video / Audio Content**: Fetch or paste clean transcripts from YouTube, lectures, or podcasts.
   - **URL / Web Essays**: Ingest via clean markdown extraction (`web_fetcher`).
2. **Deconstruct & Strip Narrative Fluff**:
   - Strip conversational filler, autobiographical anecdotes, and marketing fluff.
   - Retain core definitions, step-by-step algorithms, heuristic tables, and diagnostic rubrics.
3. **Partition into Modular Framework Units**:
   - Split multi-chapter books into independent, composable sub-skills or chapters (e.g. *The 1-Page Marketing Plan* $\rightarrow$ Prospect Phase, Lead Phase, Customer Phase).
   - Ensure individual modular units fit comfortably within targeted LLM context windows.

> **Completion criterion**: Source material deconstructed into clean, modular text sections with narrative fluff removed and key procedural passages isolated.

---

## 2. Framework & Rubric Extraction

Extract actionable procedural mechanics and mental models from the deconstructed text:

```
┌─────────────────────────────────────────────────────────────┐
│             LITERATURE EXTRACTION 4-AXIS MATRIX             │
├──────────────────────────────┬──────────────────────────────┤
│ Axis 1: Trigger & Boundaries │ Axis 2: Concrete Steps (Shu) │
│ - When to activate skill     │ - Exact operational sequence │
│ - Target problem context     │ - Mandatory input criteria   │
├──────────────────────────────┼──────────────────────────────┤
│ Axis 3: Coaching & Rubrics   │ Axis 4: Anti-Patterns & Traps│
│ - Diagnostic interview qs    │ - Negative constraints       │
│ - Grading scorecards         │ - Named failure modes        │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Axis 1 (Trigger Bounds & Problem Context)**:
   - Identify precise activation criteria: *"Under what exact conditions should this framework be invoked?"*
   - Define input requirements (e.g., target market definition, system architecture diagram).
2. **Axis 2 (The "Shu" Stage: Concrete Operational Sequence)**:
   - Formulate 3 to 5 discrete, sequential stages.
   - Ensure each stage has unambiguous, verifiable completion criteria.
3. **Axis 3 (Diagnostic Coaching Rubrics & Evaluation Scorecards)**:
   - Extract the exact diagnostic questions the author uses to test a plan or deliverable.
   - Formulate quantitative or structured criteria for evaluating whether user work satisfies the methodology.
4. **Axis 4 (Anti-Patterns & Author Warnings)**:
   - Extract explicit failure modes and common mistakes warned about in the text.
   - Pair each anti-pattern with a positive invariant rule.

> **Completion criterion**: Trigger bounds, 3-to-5 stage progression, diagnostic coaching rubrics, and named anti-patterns formulated.

---

## 3. The Visual Forge Brief

Synthesize the extracted methodology into an interactive HTML visual brief before authoring files:

1. **Target File Location**:
   - Write to `%TEMP%\book-to-skill-forge-<timestamp>.html` (Windows) or `/tmp/book-to-skill-forge-<timestamp>.html` (Unix).
2. **Styling & Standards**:
   - Dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
   - Render a **Methodology Flowchart DAG** illustrating the author's step sequence and decision branches.
   - Render the **Diagnostic Evaluation Scorecard Table** detailing evaluation criteria and passing gates.
   - Render the **Anti-Pattern Defense Matrix**.
3. **Delivery**:
   - Present the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\book-to-skill-forge-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Book to Skill Forge Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Book-to-Skill Forge Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Literature & Media Skill Synthesis</p>
  </header>
  <!-- Mermaid DAG & Scorecard Matrix -->
</body>
</html>
```

> **Completion criterion**: Self-contained HTML visual brief written to `%TEMP%`, verified non-empty, and clickable link presented to user.

---

## 4. Mandatory Checkpoint Gate

Prevent uncurated or poorly bounded skills from entering the workspace catalog:

1. Present the draft `implementation_plan.md` artifact detailing:
   - Target skill name (kebab-case): `.agents/skills/<skill-name>/`
   - Source literature attribution (Author, Title, Chapter/URL)
   - Trigger phrases for semantic intent routing
   - Formulated 5-stage progression and diagnostic coaching rubrics
   - Explicit anti-patterns and invariants
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user review and confirmation before writing files.

> **Completion criterion**: Explicit user confirmation received at the Stage 4 checkpoint.

---

## 5. Skill Graph & Card Commit

Upon user approval, scaffold the complete agent skill package and verify compliance:

1. **Scaffold Skill Files**:
   - Author `.agents/skills/<skill-name>/SKILL.md` containing frontmatter, 5-stage progression, completion criteria, and anti-patterns.
   - Author co-located `.agents/skills/<skill-name>/CARD.md` containing ASCII summary header, stage progression table, three pillars cheat sheet, and verification checklist.
2. **Execute Diagnostic Validation**:
   - Run `harness skills validate .agents/skills/<skill-name>` to assert that YAML frontmatter, stage headers, completion gates, and companion cards conform to deep-module standards.
3. **Index into Skill Knowledge Graph**:
   - Run `harness skills graph` to register the new skill node and trigger relationships into the active graph.
4. **Update Context Map**:
   - Register the new skill under the appropriate bounded domain in `CONTEXT-MAP.md`.

> **Completion criterion**: Skill package authored, companion card co-located, validation passes with zero errors, and skill graph successfully indexed.

---

## Anti-Patterns

- **Passive Summarization** — Outputting generic prose summaries instead of actionable, executable agent instructions with completion gates.
- **Context Flooding** — Dumping entire books or lengthy transcripts into context all at once instead of partitioning into modular, focused skills.
- **Shu-Stage Bypassing** — Skipping the concrete rules and diagnostic tests of the author in favor of generic, ungrounded conversational advice.
- **Missing Evaluation Rubrics** — Forging a skill that tells an agent *what* to do but provides no quantitative or structural rubric to evaluate *how well* it was done.
- **Unverified Skill Scaffolding** — Committing skills to `.agents/skills/` without running `harness skills validate` or authoring companion `CARD.md` files.
