---
name: deepen-architecture
description: Run the iterative architecture deepening loop (analyze → assess → recommend → plan → execute → verify). Use when reviewing, refining, or deepening codebase architecture, eliminating shallow modules, improving seams, or optimizing module depth.
---

# Architecture Deepening Loop

The architecture deepening loop is the continuous cadence that transforms shallow, leaky modules into deep, high-leverage abstractions with clean public seams.

Every cycle follows a strict six-stage progression:

```
[1. Analyze] → [2. Assess] → [3. Recommend (HTML)] → [4. Plan] → [5. Execute & Verify] → [6. Record]
```

See [CARD.md](CARD.md) for the skill summary card, cheatsheet, and stage-by-stage completion criteria.
Consult `/codebase-design` for the shared vocabulary of modules, interfaces, depth, seams, leverage, and locality.

---

## 1. Analyze (The Seam Audit)

Inspect the codebase to identify architectural friction points:
- **Shallow modules** — interfaces that expose internal implementation complexity rather than hiding it.
- **Leaky abstractions** — callers doing ad-hoc filesystem scans, manual dispatch loops, or duplicate instantiation.
- **Fragmented seams** — multiple subsystems implementing identical responsibilities independently.
- **Silent mutations** — state or lifecycle transitions occurring outside the audit/telemetry stream.

> **Completion criterion**: 2 to 4 concrete friction sites identified with specific file paths, line numbers, and callers.

---

## 2. Assess (The Leverage & Locality Lens)

Evaluate each candidate across three core architectural levers:

- **Locality** — Does state and its mutation logic live together in one authoritative place?
- **Leverage** — Does the interface provide substantial capability with minimal surface area (high ratio of hidden complexity to interface surface)?
- **Testability** — Can the behavior be asserted purely through public seams without reaching into internals or mocking collaborators?

Classify each candidate by recommendation strength:
- `Strong` — Clear leverage win, resolves active friction, high locality improvement.
- `Worth exploring` — Valuable architectural deepening with minor structural tradeoffs.
- `Speculative` — High conceptual elegance but adds abstraction overhead without immediate caller pressure.

> **Completion criterion**: Each candidate scored with concrete before/after architectural descriptions.

---

## 3. Recommend (The Visual Brief)

Synthesize findings into an interactive, self-contained HTML review report:

1. **Location**: Write to the OS temporary directory (`%TEMP%\architecture-review-<timestamp>.html` on Windows, `/tmp/architecture-review-<timestamp>.html` on Unix).
2. **Presentation**:
   - Use Tailwind CSS and Mermaid.js via CDN for rich visual styling and dark mode.
   - Include before/after Mermaid diagrams illustrating the shallow vs. deepened topology.
   - Display candidate cards with recommendation badges (`Strong`, `Worth exploring`, `Speculative`).
   - End with an explicit **Top Recommendation** section stating where to start and why.
3. **Communication**: Surface the absolute file path to the user with clickable links.

> **Completion criterion**: HTML report written to `%TEMP%` and path delivered to the user.

---

## 4. Plan (The Checkpoint Artifact)

Formulate an actionable, structured implementation plan:

1. Write or update `implementation_plan.md` artifact in the brain directory.
2. Group proposed edits by subsystem layer (core interfaces first, adapters second).
3. Explicitly document backward compatibility and regression risks.
4. Set `RequestFeedback: true` in artifact metadata to pause execution for user approval.

> **Completion criterion**: User explicitly reviews and approves the implementation plan.

---

## 5. Execute & Verify (Zero-Regression Seam Refactor)

Once approved, execute the refactoring in minimal, contiguous edits:

1. Implement the deep base abstraction and authoritative factory/catalog seam first.
2. Refactor existing callers and adapters to delegate to the new seam.
3. Eliminate duplicate legacy methods and ad-hoc traversal loops.
4. Execute the automated test suite (`pytest -v`) to achieve **100% pass rate** across all unit and integration tests.

> **Completion criterion**: Full test suite passes green with zero regressions and no broken public contracts.

---

## 6. Record (The Walkthrough Artifact)

Document the completed architectural improvements:

1. Update `walkthrough.md` with:
   - Summary of deepened seams and consolidated components.
   - Clickable links to all modified files and symbols.
   - Verification test metrics (test counts, execution duration, pass rate).
2. Present a concise markdown overview to the user and await the next iteration trigger.

> **Completion criterion**: `walkthrough.md` updated and presented cleanly.

---

## Anti-Patterns

- **Speculative Abstraction** — Creating deep wrappers around simple utilities that have only one trivial caller.
- **Interface Churn** — Breaking public contracts or CLI flags when deepening internal seams; always preserve public backward compatibility unless deprecation was explicitly planned.
- **Skipping Visual Verification** — Presenting raw text diffs instead of the temp HTML visual brief and Mermaid diagrams.
- **Proceeding Without Plan Approval** — Executing code refactors before the user reviews and signs off on `implementation_plan.md`.
