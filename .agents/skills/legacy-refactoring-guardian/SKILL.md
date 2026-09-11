---
name: legacy-refactoring-guardian
description: Execute safe legacy codebase modernization using AI-assisted codebase archaeology, characterization testing safety nets, and incremental refactoring loops. Do not use for greenfield project scaffolding or hasty rewrites.
---

# Legacy Refactoring Guardian: Codebase Archaeology & Characterization Safety Nets

`legacy-refactoring-guardian` is an autonomous engineering discipline and agent workflow designed to prevent the single most dangerous failure mode in software modernization: **changing legacy code before understanding its existing observable behavior**.

Synthesized from Hugo Teijiz's foundational literature (*"How to Understand a Legacy Codebase Using AI Before Changing it"* and *"How to Build Characterization Tests Before Refactoring Legacy Code"*, freeCodeCamp, 2026), this skill establishes a rigorous two-phase protocol:
1. **Codebase Archaeology**: Using AI and AST tooling to map real repository paths, trace business capabilities end-to-end, disentangle business rules from infrastructure, discover implicit contracts, and record explicit unknowns—all verified against a 5-level evidence hierarchy.
2. **Characterization Testing**: Constructing temporary executable knowledge infrastructure that captures what the software *does today* across happy paths, critical edge cases, and external side effects—strictly prohibiting AI from inventing expected behavior—before executing micro-step refactors behind mechanical seams.

Every legacy modernization task must execute this 5-stage progression:

```
[1. Repository Mapping & Scoping] → [2. Execution Tracing & Seams] → [3. Visual Forge Brief] → [4. Checkpoint & Characterization] → [5. Micro-Refactor & Maturation]
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and verification checklist.
Consult `references/seam-catalog.md` for Michael Feathers' seam catalog, `references/evidence-validation-playbook.md` for query recipes, and `examples/legacy-billing-service/` for an end-to-end modernization exemplar.
Related skills: `/crafting-skills` for craft guidelines, `/adversarial-agent-verifier` for seam verification, and `/deepen-architecture` for structural deepening.

---

## Configuration Precedence & Settings

Configuration resolves via standard 3-tier layering:
1. **Workspace Config**: `<workspace_root>/.agents/skills.config.yaml`
2. **Skill Defaults**: `.agents/skills/legacy-refactoring-guardian/config.default.yaml`
3. **Hardcoded Invariants**: Conservative built-in fallbacks.

Key configuration keys include `test_framework` (`pytest` / `jest`), `max_ast_depth`, `capture_side_effects`, and `boundary_test_values`.

---

## 1. Repository Mapping & Capability Scoping

Before reading class bodies or proposing refactorings, map the macro landscape and bound the blast radius to a single capability:

1. **Map High-Level Repository Architecture**:
   - Identify active entry points (HTTP routers, CLI commands, background consumers, scheduled cron jobs).
   - Locate persistence layers (ORM models, migration scripts, raw SQL helpers), external client integrations, and configuration files.
   - Do **NOT** initiate code transformations or architectural redesigns during repository mapping.
2. **Isolate Exactly One Business Capability**:
   - Select a concrete, observable workflow (e.g. `Approve Order`, `Register Customer`, `Calculate Premium Discount`, `Cancel Subscription`).
   - Resist the temptation to modernize entire modules or multiple subsystems at once.
3. **Bound Inputs and Observable Exit Points**:
   - Identify the exact triggering input shapes and external outputs.

> **Completion criterion**: Target repository landscape mapped, modernization bounded strictly to one business capability, and blast radius contained.

---

## 2. End-to-End Tracing & Seam Identification

Trace execution flow through the codebase and prepare isolated test boundaries without modifying domain logic:

1. **Execute Deterministic AST Tracing**:
   - Run the bundled AST archaeologist tool to trace the capability:
     ```bash
     python .agents/skills/legacy-refactoring-guardian/scripts/legacy_archaeologist.py --file <path_to_source> --function <function_name>
     ```
   - Automatically extracts function parameters, call hierarchies, side effects, and complexity.
2. **Disentangle Rules from Infrastructure**:
   - Separate explicit business rules (discount thresholds, fee calculations, validation gates) from infrastructure mechanisms (database transactions, serialization, HTTP headers).
   - Distinguish *confirmed business rules* from *probable heuristics* and *infrastructure artifacts*.
3. **Discover Implicit Contracts**:
   - Run with contract detection enabled:
     ```bash
     python .agents/skills/legacy-refactoring-guardian/scripts/legacy_archaeologist.py --file <path_to_source> --function <function_name> --json
     ```
   - Catalogs outputs consumed outside the module: API payload fields, emitted event schemas, queue messages, database column formats, CSV exports, error codes, and log strings parsed by downstream telemetry.
4. **Group Semantic Duplication Without Premature Unification**:
   - Group semantically related rules across modules, but do **NOT** merge them. Duplication often represents independent domains that evolved separately.
5. **Enforce the 5-Level Evidence Validation Hierarchy**:
   - Consult `references/evidence-validation-playbook.md` to validate every AI finding against ground truth:
     1. *Repository Search / AST*: `rg "methodName" .` to confirm call sites and references.
     2. *Existing Tests*: Inspect fixtures, boundary assertions, and expected errors.
     3. *Database Schema*: Inspect foreign keys, nullability, defaults, and legacy columns.
     4. *Logs & Telemetry*: Verify whether code paths are actively executed in production.
     5. *Git Version History*: `git log -S` and `git blame` to uncover why strange conditions were created.
6. **Introduce Minimal Mechanical Seams (Michael Feathers Seam Concept)**:
   - Consult `references/seam-catalog.md` for seam archetypes.
   - If database or network coupling blocks direct test execution, introduce a minimal mechanical seam (e.g. parameter injection or repository interface adapter).
   - **Strict Invariant**: Keep seam creation purely mechanical. Do not redesign or clean up business logic while introducing test seams.

> **Completion criterion**: End-to-end execution path documented, implicit contracts cataloged, findings validated via the 5-level evidence hierarchy, and minimal mechanical seams prepared.

---

## 3. The Visual Forge Brief

Synthesize the archaeological findings into an interactive HTML visual brief before authoring test suites or touching production code:

1. **Target File Location**:
   - Write to `%TEMP%\legacy-refactoring-guardian-<timestamp>.html` (Windows) or `/tmp/legacy-refactoring-guardian-<timestamp>.html` (Unix).
2. **Styling & Standards**:
   - Dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
   - Embed the generated Mermaid DAG from the archaeologist:
     ```bash
     python .agents/skills/legacy-refactoring-guardian/scripts/legacy_archaeologist.py --file <path_to_source> --function <function_name> --mermaid
     ```
   - Render the **Observable Contracts & Side Effects Table**.
   - Render the **Unknowns & Risk Registry**.
   - Render the **Anti-Pattern Defense Matrix**.
3. **Delivery**:
   - Present the absolute, clickable HTML file path to the user.

> **Completion criterion**: Self-contained HTML visual brief written to `%TEMP%`, verified non-empty, and clickable link presented to user.

---

## 4. Mandatory Checkpoint Gate & Characterization Harness

Prevent unverified assumptions from breaking production by establishing the characterization safety net:

1. **Present the Checkpoint Plan**:
   - Author draft `implementation_plan.md` artifact detailing:
     - Target capability and test boundary (function, module, or service).
     - Observable behaviors and explicit evidence sources.
     - Planned characterization test suite file path.
     - Known anomalies and unanswered questions.
   - Set `RequestFeedback: true` in artifact metadata.
   - **STOP and wait** for explicit user review and confirmation.
2. **Synthesize Characterization Tests with Zero Hallucination**:
   - Execute the bundled characterization test generator:
     ```bash
     python .agents/skills/legacy-refactoring-guardian/scripts/char_test_harness.py --file <path_to_source> --func <function_name> --emit tests/test_char_<function_name>.py
     ```
   - Automatically executes boundary input matrices (zero amounts, empty arrays, nulls, negative numbers, threshold values) against the live code to capture **actual runtime outputs**.
   - Capture observable side effects: database updates, queued events, message publishes, and audit log emissions.
3. **AI Hallucination Defense (Critical Negative Boundary)**:
   - **NEVER** let AI invent expected behavior based on what seems "reasonable" (e.g. assuming `age >= 65` when the code explicitly evaluates `age > 65`).
   - Derive expected values strictly from running executable code, fixtures, database snapshots, or historical test fixtures.

> **Completion criterion**: User approval received at checkpoint, and characterization test suite green against existing legacy code with all side effects protected.

---

## 5. Anomaly Quarantine, Micro-Refactoring & Maturation

Execute safe structural modernization under the protection of the characterization harness:

1. **Quarantine Discovered Bugs & Behavioral Anomalies**:
   - When characterization reveals code that appears clearly buggy (e.g. charging a fee for zero-value transactions), separate two distinct questions:
     1. *What does the system do today?* (Lock in characterization test).
     2. *What should the system do?* (Log for business clarification).
   - **Strict Invariant**: Never fix bugs silently during a refactoring branch. Downstream consumers may rely on the quirk. Document the current behavior first, confirm with stakeholders, and patch defects in a dedicated, isolated commit.
2. **Maintain the Explicit Unknowns Registry**:
   - Document all unanswered architectural questions (e.g. *"Is legacy_id still read by downstream ERP?"*). Block migration steps that cross unverified boundaries.
3. **Execute the Micro-Refactoring Cycle**:
   - Make exactly **one** structural change at a time (e.g. extract method, decouple dependency, introduce value object).
   - Run the full characterization suite immediately after the change.
   - If tests fail, revert or fix the regression before touching any other code.
   - Commit each structural step atomically with clear diffs.
4. **Graduate Characterization Tests to Specification Tests**:
   - As understanding matures, update tests from documenting observed behavior (`it("currently returns 0 when balance is null")`) to asserting verified domain specifications (`it("clamps null balance to zero per accounting rule BR-104")`).

> **Completion criterion**: Modernization completed via micro-steps with zero behavioral regressions, defects properly quarantined, and characterization tests graduated to specification tests.

---

## Diagnostic Coaching Rubrics

When reviewing or executing a legacy refactoring workflow, evaluate against these diagnostic interview questions:

1. **The Preservation Test**: *"Did I preserve the behavior that already mattered?"*
2. **The Observability Test**: *"If this behavior changed during refactoring, could somebody outside this function or service notice?"*
3. **The Evidence Test**: *"Does this expected test result come from running code and system evidence, or did AI invent what seemed reasonable?"*
4. **The Structural Leakage Test**: *"Are we testing observable behavior, or are we freezing implementation details (private methods, temporary variable names) that will block future cleanups?"*
5. **The Seam Discipline Test**: *"Is the introduced seam purely mechanical, or did we prematurely redesign domain logic while trying to create a test boundary?"*
6. **The Anomaly Test**: *"Did we silently fix a legacy bug during refactoring, or did we characterize it and isolate the defect for business sign-off?"*

---

## Practical AI Directives & Prompts

### Prompts to STRICTLY AVOID at Project Inception:
- ❌ *"Rewrite this application using Clean Architecture."*
- ❌ *"Convert this monolith into microservices."*
- ❌ *"Find all the bad code and fix it."*
- ❌ *"Modernize this entire repository."*

*Rationale*: These prompts presuppose solutions before establishing what existing business rules matter.

### Prompts to USE for Rigorous Archaeology:
- ✅ *"Identify outputs from this module that could be consumed outside the module (HTTP responses, emitted events, queue messages, database records, files, logs). For each, explain what evidence suggests an implicit contract."*
- ✅ *"For each candidate characterization test, tell me how I can obtain the expected result from the current implementation. Do not propose the expected result yourself unless derived from executable runs or fixtures."*
- ✅ *"Based on everything analyzed so far, list the questions that cannot be answered safely from the repository alone. Focus on questions that impact refactoring, migration, or removal. Do not answer them."*

---

## Anti-Patterns

- **Inventing Expected Behavior** — Allowing AI or developer intuition to guess what the software should do rather than capturing what it currently does.
- **Premature Target Architecture** — Prompting for "Clean Architecture" or "Microservices" before mapping existing rules, contracts, and dependencies.
- **Freezing Implementation Details** — Writing characterization assertions against private helper names, internal object shapes, or specific call orders that block refactoring.
- **Stealth Bug Fixing** — Silently altering legacy oddities during a refactoring branch instead of isolating them in dedicated commits.
- **Accidental Duplication Unification** — Prematurely merging syntactically similar code across modules without business evidence that domains are identical.
- **Batch Structural Modernization** — Making multiple architectural changes simultaneously, rendering test regression diagnosis impossible.
