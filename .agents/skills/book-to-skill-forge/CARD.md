# Skill Summary Card: `book-to-skill-forge`

```
╔════════════════════════════════════════════════════════╗
║               SKILL SUMMARY CARD                       ║
╠════════════════════════════════════════════════════════╣
║ SKILL:       book-to-skill-forge                       ║
║ Category:    integration_and_io / skill-synthesis      ║
║ Invocation:  /book-to-skill-forge                      ║
║ Trigger:     "turn a book into a skill",               ║
║              "convert article to skill",               ║
║              "forge skill from literature",            ║
║              "video to skill", "book to skill"         ║
║ Version:     1.0.0                                     ║
║ Provides:    "literature_skill_synthesis"              ║
╠════════════════════════════════════════════════════════╣
║ Target:      Transform books, articles, and video      ║
║              transcripts into executable deep-module   ║
║              agent skills with coaching rubrics.       ║
╚════════════════════════════════════════════════════════╝
```

---

## The 5-Stage Literature Synthesis Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Ingest & Deconstruct** | Ingest source text/video transcript and strip narrative fluff | Modularized markdown sections | Fluff removed, key procedural steps isolated |
| **2. Framework & Rubrics** | Extract trigger bounds, Shu-stage steps, coaching rubrics, anti-patterns | 4-Axis extraction matrix | Concrete steps, diagnostic questions, anti-patterns mapped |
| **3. The Visual Brief** | Render interactive HTML Visual Brief in `%TEMP%` with Mermaid DAGs | HTML Visual Brief | Visual brief generated and clickable link delivered |
| **4. Mandatory Checkpoint** | Author `implementation_plan.md` with `RequestFeedback: true` | Implementation Plan | Explicit human confirmation received |
| **5. Skill & Card Commit** | Scaffold `SKILL.md` + `CARD.md`, validate, and index into Skill Graph | Validated Skill Package | Passes `harness skills validate` and indexed in graph |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\book-to-skill-forge-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Methodology Flowchart & Diagnostic Scorecards -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit user approval before authoring files.
```

### 3. Explicit Anti-Patterns Box
- **Passive Summarization**: Generating static text summaries rather than executable agent instructions.
- **Context Flooding**: Overloading context windows with whole books instead of modular chapters.
- **Shu-Stage Bypassing**: Providing generic advice rather than adhering to author's concrete framework.
- **Missing Evaluation Rubrics**: Failing to specify how to grade deliverables against the author's standards.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Instructions state direct target actions instead of negative prohibitions.
- [ ] **Leading Words**: Employs compact domain vocabulary (*seam*, *depth*, *rubric*, *deconstruction*, *checkpoint*, *brief*).
- [ ] **Exhaustive Completion Criteria**: Every stage specifies unambiguous completion conditions.
- [ ] **Modular Boundaries**: Books partitioned into focused, composable chapters/sub-skills.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored and linked from `SKILL.md`.
- [ ] **Pre-Flight Validation**: Passes `harness skills validate` with zero errors.
