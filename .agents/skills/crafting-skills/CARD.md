# Skill Summary Card: `crafting-skills`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        crafting-skills                           │
│ Category:    engineering / meta-skills                 │
│ Invocation:  /crafting-skills                          │
│ Trigger:     "craft a skill", "refactor this skill",   │
│              "author skill", "upgrade skill design"    │
│ Version:     1.0.0                                     │
│ Provides:    "skill_crafting"                          │
├────────────────────────────────────────────────────────┤
│ Target:      Author and refactor agent skills into     │
│              high-precision, deep-module blueprints    │
│              with visual briefs and checkpoints.       │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Authoring & Refactoring Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Target & Seams** | Define domain boundaries, kebab-case name, and triggers | Frontmatter draft | Front-loaded description with zero bloat |
| **2. Information Hierarchy** | Structure sequential steps, in-file reference, and disclosed pointers | Document skeleton | Clear separation of sequence from reference |
| **3. Core Mechanics** | Inject Visual Brief (Temp HTML), Checkpoint (`RequestFeedback`), Anti-Patterns | Core skill body | Three pillars explicitly embedded |
| **4. Companion Card** | Author `CARD.md` with ASCII header, stage table, and invariants | `CARD.md` co-located | Card authored and linked from `SKILL.md` |
| **5. Verification** | Audit against positive phrasing, leading words, and completion gates | Final validated skill | Passes all 4 verification checks |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\<skill-name>-review-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Interactive Before vs. After Mermaid Diagrams -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit user approval before execution.
```

### 3. Explicit Anti-Patterns Box
- **Speculative Abstraction**: Designing for imaginary future requirements rather than concrete current friction.
- **Interface Churn**: Redesigning working seams without measurable locality or leverage gains.
- **Premature Completion**: Exiting a workflow before all verification tests and artifacts are delivered.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Direct target actions instead of negative prohibitions.
- [ ] **Leading Words**: Compact pretrained vocabulary (*seam*, *depth*, *leverage*, *locality*, *brief*, *checkpoint*).
- [ ] **Exhaustive Completion Criteria**: Every step has an unambiguous done-state.
- [ ] **No Monolithic Bloat**: Reference disclosed behind companion files (`CARD.md`, `REFERENCE.md`).
- [ ] **Companion Card Present**: Co-located `CARD.md` created and linked.
