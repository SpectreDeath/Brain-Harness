---
name: codebase-context-architect
description: Architect, synchronize, budget, and verify multi-layer codebase context files (AGENTS.md, CLAUDE.md, .cursor/rules/). Implement single-source generators, automated CI linters, and post-tool hooks to eliminate context rot. Do not use for generic prompt writing or marketing documentation.
---

# Codebase Context Architect

`codebase-context-architect` is the repository engineering and context governance engine for managing AI agent context files across complex codebases. It operationalizes foundational principles from Kayode Adeniyi (*How to Manage Context Files in Your Codebase and Get Better Output From AI Coding Agents*, freeCodeCamp / MCF) and Anthropic's context engineering research.

It eliminates **Context Rot**, **Kitchen Sink Bloat**, and **Vendor Fork Divergence** by structuring repository instructions into a **Three-Layer Context Architecture**, synchronizing multi-tool formats from a canonical Single Source of Truth (`AGENTS.md`), and enforcing automated CI verification linters that fail builds on broken paths, dead scripts, and budget blowouts.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression table, and invariants checklist.
Consult `/agent-skills-architect` for enterprise skill design, `/agent-skill-sdlc` for lifecycle management, `/agent-instruction-architect` for instruction smell auditing, [three-layers-architecture.md](references/three-layers-architecture.md) for architectural partitioning, and [context-linter-guide.md](references/context-linter-guide.md) for automated CI verification.

---

## The 5-Stage Context Architecture Progression

```
[1. Layered Partitioning & Removal Test] ──► [2. SSOT Generation & Vendor Sync] ──► [3. Altitude & Deliberate Absences]
                                                                                               │
                                                                                               ▼
[5. Empirical Benchmarks & DoD Feedback] ◄── [4. Automated Context Verification & CI] ◄────────┘
```

---

## 1. Layered Context Partitioning & Removal Test

Treat context files as a **finite budget allocation problem** before a documentation problem:

1. **Partition Context into Three Discrete Layers**:
   - **Layer 1: Always Loaded Root (`AGENTS.md`)**:
     - Read at the start of every session regardless of task.
     - Budget ceiling: strictly bounded to $\le 800$ tokens (~3,200 characters).
     - Contains only repository-wide invariants, essential development loop commands, and non-obvious conventions.
   - **Layer 2: Scoped Subdirectory Files (`src/AGENTS.md`, `.cursor/rules/*.mdc`)**:
     - Loads only when the agent operates within a specific subdirectory or touches matching file globs.
     - Budget ceiling: strictly bounded to $\le 400$ tokens (~1,600 characters).
     - Houses domain-specific rules (e.g., API handler contracts, frontend state stores, test isolation).
   - **Layer 3: On-Demand Pointers (`docs/`, `skills/`)**:
     - Costs only a few tokens in the root file as path references (`docs/architecture.md`, `docs/testing.md`, `docs/decisions/`).
     - Agents pull the underlying detailed documentation into context only when a specific task requires it.
2. **Apply the Strict Line Removal Test**:
   - For every line considered for inclusion, ask:
     > *"Would removing this line cause the agent to make a mistake?"*
   - If the answer is **no**, purge the line immediately.
   - Eliminate basic language explanations (e.g. `const` vs `var`), directory walk descriptions visible from the tree, and generic platitudes.

> **Completion criterion**: Context partitioned across 3 layers with always-loaded files under token budgets and non-essential prose pruned.

---

## 2. SSOT Generation & Vendor Synchronization

Eliminate vendor divergence by declaring canonical `AGENTS.md` as the sole human-edited source of truth:

1. **Establish the Canonical Source of Truth**:
   - Author all root instructions in `AGENTS.md` adhering to the Linux Foundation / Agentic AI Foundation standard.
2. **Automate Downstream Vendor File Generation**:
   - Use `harness context sync` (or `python scripts/sync_context.py` / `CodebaseContextEngine.sync()`):
     - **Claude Code (`CLAUDE.md`)**:
       - Leverage Claude Code's `@` file import syntax (`@AGENTS.md`).
       - Append only tool-specific operational rules (`CLAUDE_EXTRAS`, e.g., plan mode triggers, subagent delegation preferences).
       - Keeps `CLAUDE.md` compact ($\le 150$ tokens).
     - **GitHub Copilot (`.github/copilot-instructions.md`)**:
       - Inlines canonical `AGENTS.md` content with a prominent generated banner.
     - **Cursor (`.cursor/rules/*.mdc`)**:
       - Generate glob-scoped `.mdc` files with YAML frontmatter specifying directory match globs (`globs: "src/**/*.ts"`).
3. **Embed Anti-Tamper Warning Banners**:
   - Inject a visible header comment into all generated files:
     ```markdown
     <!-- Generated from AGENTS.md by `harness context sync`. Edit AGENTS.md instead. -->
     ```
   - Wire CI checks to fail if generated files are edited directly without running the synchronizer (`harness context sync --dry-run`).


> **Completion criterion**: Canonical AGENTS.md authored, downstream generator script configured, and vendor files synchronized with zero manual duplication.

---

## 3. Altitude Calibration & Deliberate Absences

Calibrate instruction altitude and protect architectural choices from speculative agent additions:

1. **Calibrate Instruction Altitude**:
   - Avoid **Rigid Brittleness** (line-level micro-rules that shatter on the first valid exception).
   - Avoid **Vague Encouragement** ("write clean, maintainable code" which changes zero agent decisions).
   - Follow the **Three-Part Altitude Formula**:
     1. **Pattern Shape**: Describe the structural role of the module (e.g., *"Handlers parse and validate input, then delegate to services"*).
     2. **Explicit Boundary**: State the hard negative boundary (e.g., *"Handlers never touch the database store directly"*).
     3. **Worked Example Link**: Point to an existing file demonstrating the pattern (e.g., *"See `src/api/tasks.js` for the pattern to copy"*).
2. **Attach Positive Rationales to Rules**:
   - State the reason behind non-obvious constraints (*"Handers return error codes rather than HTTP statuses because `router.js` owns status mapping"*).
   - Rules with attached reasons survive novel situations unpredicted by the rule author.
3. **Document Deliberate Absences in ADRs**:
   - Capture deliberate omissions in Architecture Decision Records (`docs/decisions/`).
   - Explicitly instruct the agent that missing infrastructure is an intentional design choice rather than a gap to fill (e.g., *"This service uses an in-memory store by design; do not introduce Postgres, SQLite, or an ORM"*).

> **Completion criterion**: Instructions calibrated with pattern shapes, negative boundaries, worked examples, and ADR intentional absences documented.

---

## 4. Automated Context Verification & CI Gating

Prevent silent context rot by treating context files like executable code verified by automated linters:

1. **Execute the 4-Check Context Linter (`harness context lint` / `CodebaseContextEngine.lint()`)**:
   - **Check 1: Token Budget Ceilings**:
     - Estimate token counts across always-loaded files using calibrated character heuristics.
     - Flag any file approaching or exceeding its budget ceiling.
   - **Check 2: Prose Inline Path Integrity**:
     - Strip fenced markdown codeblocks (` ```...``` `).
     - Extract all backtick inline code spans resembling paths (` `src/services/tasks.py` `).
     - Assert that every referenced path exists on disk (`Path.exists()`).
   - **Check 3: Script Command Validity**:
     - Extract all mentioned script invocations (e.g., `npm test`, `pytest`, `ruff check`).
     - Verify against declared scripts in `package.json`, `pyproject.toml`, or `Makefile`.
   - **Check 4: Generator Sync Drift**:
     - Re-run `harness context sync --dry-run` or `sync_context.py --dry-run`.
     - Fail if on-disk vendor files differ by even a single character from canonical generation.
2. **Wire into CI Pipelines & Git Hooks**:
   - Add context linting to GitHub Actions / CI workflow:
     ```yaml
     - name: Verify Codebase Context Files
       run: harness context lint --root .
     ```
   - Wire pre-commit hooks to block commits containing broken paths or drifted vendor files.


> **Completion criterion**: Context linter passes with exit code 0, 0 broken paths, 0 missing scripts, and zero sync drift.

---

## 5. Empirical Benchmarking & Definition of Done Feedback

Ground agent execution with deterministic feedback loops and objective validation:

1. **Formulate Verifiable Definitions of Done**:
   - Never allow an agent to declare a task finished based on "looks completed".
   - Mandate specific test/lint execution commands in the root file.
   - **Require Evidence**: Demand that the agent paste the actual terminal output rather than claiming success in prose.
2. **Install PostToolUse Agent Hooks**:
   - Where supported by the client harness (e.g. Claude Code `.claude/settings.json`), install `PostToolUse` hooks on `Edit|Write` actions that silently run context linting:
     ```json
     {
       "hooks": {
         "PostToolUse": [
           {
             "matcher": "Edit|Write",
             "hooks": [
               {
                 "type": "command",
                 "command": "python scripts/context_linter.py --silent"
               }
             ]
           }
         ]
       }
     }
     ```
3. **Execute Empirical A/B Benchmarks**:
   - Validate context file ROI by testing a standardized feature implementation prompt under two conditions:
     - **Branch A**: With full multi-layer context files active.
     - **Branch B**: With context files deleted (baseline).
   - Score the delta along 4 objective metrics:
     1. Test pass rate on first attempt.
     2. Number of human interventions/corrections required.
     3. Adherence to architectural boundaries and layering.
     4. Zero unapproved third-party dependencies introduced.

> **Completion criterion**: Definition of done enforced with pasted evidence, post-tool hooks wired, and empirical A/B validation completed.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every major context restructuring or repository onboarding session must synthesize the context topology into an interactive HTML visual brief in `%TEMP%` loading Tailwind CSS and Mermaid.js via CDN. The brief visualizes the 3 layers, token budgets, and linter status.

### 2. The Mandatory Checkpoint Gate Pillar
When re-architecting repository context files, partitioning rules, or configuring CI gates, author an `implementation_plan.md` artifact with `RequestFeedback: true`. The agent must **STOP and wait** for explicit developer review and approval before mutating workspace files.

### 3. Explicit Anti-Patterns
Rigid behavioral boundaries must be maintained to prevent context rot, instruction pollution, and ungrounded agent drift.

---

## Anti-Patterns

- **Kitchen Sink Bloat** — Inlining generic tutorials, language default lessons, or team history into root files, exhausting model attention budgets.
- **Silent Context Rot** — Allowing stale backtick paths and deleted scripts to linger because no CI check or pre-commit hook verifies them.
- **Vendor Fork Divergence** — Maintaining separate hand-edited copies of CLAUDE.md, AGENTS.md, and Copilot instructions that contradict each other.
- **Vague Encouragement Trap** — Stating ungrounded platitudes ("write maintainable code") instead of concrete boundaries, patterns, and worked examples.
- **Inlined Monolith Sprawl** — Inlining multi-page architecture guides and schemas into root instructions instead of pointing to on-demand docs.
- **Unverifiable Looks-Done Exit** — Allowing agents to finish tasks without running concrete test/lint commands and pasting verifiable CLI output evidence.
