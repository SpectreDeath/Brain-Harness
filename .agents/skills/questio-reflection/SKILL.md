---
name: questio-reflection
description: Mandate Aquinas-style adversarial self-reflection before executing destructive, structural, or irreversible operations. Use when the user asks to stress-test a plan, conduct an adversarial review, run a questio check, self-critique a refactoring proposal, or test architectural invariants before execution.
---

# Questio Adversarial Reflection Engine

The `questio-reflection` engine operationalizes the classical Aquinas *disputed question* method as an autonomous adversarial pre-commit gate. It subjects any proposed implementation, refactoring, or database mutation to systematic self-critique before code is modified.

Every questio cycle follows a strict five-stage progression:

```
[1. Propositio (Thesis)] → [2. Videtur Quod Non (Objections)] → [3. Sed Contra (Grounding)] → [4. Visual Brief (Temp HTML)] → [5. Respondeo (Hardening & Checkpoint)]
```

See [CARD.md](CARD.md) for the quick-reference cheat sheet, stage progression matrix, and completion criteria.
Consult `/crafting-skills` for the underlying design standard and pillar specifications.

---

## 1. Propositio (The Thesis & Blast Radius)

Formulate a concise, unambiguous statement of the proposed action:
1. **Core Thesis**: Define the exact architectural change, public seam modification, or state mutation.
2. **Blast Radius**: List all modules, test suites, and data models directly or transitively affected.
3. **Primary Invariants**: State the system invariants that must remain unchanged throughout execution.

> **Completion criterion**: A single markdown block declaring the thesis, touched files with clickable links, and candidate blast radius.

---

## 2. Videtur Quod Non (The Tri-Vector Objections)

Construct the strongest possible case *against* the proposed plan by formulating three high-impact adversarial objections across distinct failure vectors:

1. **Vector A — Architectural Seam & Coupling**:
   - How could this introduce hidden cyclic dependencies, leak private abstractions, or break inversion of control?
2. **Vector B — Runtime, Async & Hardware Resilience**:
   - How could this fail under concurrent access, async event loops, subprocess sandboxes, or resource exhaustion?
3. **Vector C — Epistemic Drift & Unverified Assumptions**:
   - What assumptions in this plan rely on unverified assumptions, cached knowledge, or missing edge-case testing?

> **Completion criterion**: 3 steel-manned, non-trivial objections identified with concrete failure scenarios.

---

## 3. Sed Contra (The Counter-Grounding)

Anchor the viability of the proposal against verified ground truth in the current workspace:
1. Inspect authoritative codebase references using `view_file` or `grep_search`.
2. Cite explicit file locations and line ranges: `[module.py:L15-L32](file:///d:/path/to/module.py#L15-L32)`.
3. Discard any argument that cannot be substantiated by active source lines or verified test assertions.

> **Completion criterion**: Every counter-grounding premise explicitly linked to a verified file URI and line range.

---

## 4. Recommend (The Visual Adversarial Brief)

Synthesize the thesis, objections, and counter-grounding into an interactive HTML visual brief:

1. **Target Path**: Write to `%TEMP%\questio-review-<timestamp>.html` (Windows) or `/tmp/questio-review-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
   - Include a Mermaid **Attack Tree vs. Mitigation Topology** comparing failure vectors with defensive guards.
   - Render candidate objection cards with severity badges (`Critical`, `Structural`, `Runtime`).
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\questio-review-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Questio Adversarial Review</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Questio Pre-Commit Adversarial Gate</h1>
    <p class="text-sm text-gray-400 mt-1">Aquinas Adversarial Reflection Report</p>
  </header>
  <!-- Interactive Attack Tree & Objection Matrix -->
</body>
</html>
```

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 5. Respondeo (Hardening & Mandatory Checkpoint)

Refactor the implementation plan to systematically resolve all three objections:

1. Update or create the `implementation_plan.md` artifact.
2. For each objection in Stage 2, embed a concrete defensive guard (e.g., fallback seam, lock, assertion, sandbox boundary).
3. Set `RequestFeedback: true` in artifact metadata.
4. **STOP and wait** for explicit user approval before executing any destructive or mutating commands.

```markdown
### [Questio Resolution Block]
- **Target Seam**: `[ServiceRegistry](file:///path/to/registry.py)`
- **Objection 1 (Coupling)**: `<failure mode>` → **Mitigation**: `<defensive guard>`
- **Objection 2 (Runtime)**: `<failure mode>` → **Mitigation**: `<defensive guard>`
- **Objection 3 (Epistemic)**: `<failure mode>` → **Mitigation**: `<defensive guard>`
- **Pre-Commit Verdict**: [APPROVED / REVISE]
```

> **Completion criterion**: Implementation plan updated with explicit objection resolutions and user approval received.

---

## Anti-Patterns

- **Strawman Objections** — Formulating trivial, easily dismissed objections (e.g., "typos might occur") instead of probing severe structural failure modes.
- **Phantom Grounding** — Citing conceptual patterns without linking to active code lines (`file:///...#Lxx-Lyy`).
- **Unmitigated Invariants** — Proceeding with a plan when one or more objections remain unresolved.
- **Rubber-Stamping** — Generating the questio block as after-the-fact commentary rather than a blocking pre-commit gate.
