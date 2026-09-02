---
name: adversarial-agent-verifier
description: Execute rigorous runtime verification including DAG-based component seam analysis, inspect-before-edit protocols, test-driven contracts, and harsh adversarial code reviews demanding git diffs. Trigger when reviewing AI-generated code, preparing pull requests, conducting pre-merge audits, stress-testing complex refactors, or running clean-up commits.
---

# Adversarial Agent Verifier

`adversarial-agent-verifier` is the quality assurance and adversarial verification engine for agentic workflows. Because AI models default to polite, non-critical feedback and generate code with subtle seam vulnerabilities in up to 40% of cases, this engine enforces the **Adversarial Verification Protocol**: non-modifying inspection, DAG-based seam analysis (Michael Feathers seams), test-driven contracts, harsh rubric scoring (1–10 severity scale), and clean-up audits.

Every adversarial verification session executes this five-stage progression:

```
[1. Inspect-Before-Edit Seam Triage] → [2. DAG Component Seam Analysis] → [3. Test-Driven Contract Authoring] → [4. Minimal-Diff Implementation] → [5. Adversarial Review & Clean-Up Commit]
```

See [CARD.md](CARD.md) for the companion summary card, prompt catalog, and verification rubrics.
Consult `/code-review` for PR standards and `/questio-reflection` for Aquinas-style adversarial reflection.

---

## 1. Inspect-Before-Edit Seam Triage

Halt immediate code modification and force repository inspection before writing changes:

```
┌─────────────────────────────────────────────────────────────┐
│                INSPECT-BEFORE-EDIT PROTOCOL                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Locate: Which files control the target subsystem?        │
│ 2. Trace: Where does the root cause / edge case live?       │
│ 3. Inventory: What existing tests cover this boundary?      │
│ 4. Boundary: What is the smallest safe diff to fix it?      │
│ 5. Constraint: Modify ZERO files until summary is approved. │
└─────────────────────────────────────────────────────────────┘
```

1. **Execute Inspection Prompt**:
   - For non-trivial bugs or refactors, enforce the inspect-first directive:
     > *"Before editing any files, inspect the repository and summarize: (1) which files control this subsystem, (2) where the bug likely lives, (3) what tests cover this area, and (4) the smallest safe change. Do not modify files until after this summary."*
2. **Prevent Shotgun Editing**:
   - Prevent the failure mode where the agent creates 10 unnecessary files in the wrong location because it acted before locating the architectural seam.

> **Completion criterion**: Non-modifying inspection summary produced, identifying root cause file, covering tests, and smallest safe diff.

---

## 2. DAG Component Seam Analysis

Model application workflows as Directed Acyclic Graphs (DAGs) to identify high-risk component boundaries (Michael Feathers *seams*):

1. **Map System Workflow as a DAG**:
   - Identify nodes (data models, service handlers, database adapters, API routes).
   - Identify directed edges (function calls, network requests, message bus events).
2. **Isolate Seam Vulnerabilities**:
   - Pinpoint high-risk seams where components interface:
     - Serialization/Deserialization boundaries.
     - Database transaction boundaries and rollbacks.
     - External network calls and timeout handling.
     - Permission and compliance gates.
     - Markdown token delimiter boundaries (parsing commands or references wrapped in backticks `` ` `` or brackets `[`).
3. **Generate Seam Opportunity Table**:
   - Produce a prioritized table of integration test opportunities ranked by risk and blast radius.

```
| Seam ID | Origin Node | Destination Node | Risk Factor | Proposed Test Assertion |
| :--- | :--- | :--- | :--- | :--- |
| S-01 | AuthHandler | TokenService | Token Expiry Race | Expired token returns 401, not 500 |
| S-02 | PaymentEngine | LedgerDB | Transaction Abort | Failed stripe charge rolls back ledger row |
```

> **Completion criterion**: Workflow DAG mapped and prioritized Seam Opportunity Table generated.

---

## 3. Test-Driven Contract Authoring

Make tests the immutable contract before writing production code:

1. **Author Failing Tests First (Red Stage)**:
   - Write unit or integration tests that precisely reproduce the reported bug or assert the new feature behavior.
   - Run the test suite to confirm tests fail with the expected error.
2. **Lock the Test Contract**:
   - Do not modify the test assertions during implementation unless the test specification itself is demonstrably flawed.
3. **Execution Directive**:
   > *"Write failing tests first for this bug. Confirm they fail. Then implement the smallest fix. Do not modify the tests after implementation. Run the relevant test suite before finishing."*

> **Completion criterion**: Failing tests authored, failure mode confirmed, and test contract locked.

---

## 4. Minimal-Diff Implementation

Implement the fix strictly bounded by the test contract and architectural constraints:

1. **Smallest Safe Diff**:
   - Restrict code modifications exclusively to the located root cause seam.
   - Avoid speculative abstractions, unnecessary helper classes, or refactoring unrelated files.
2. **Dependency Guardrail**:
   - Zero new production dependencies without prior review.
3. **Run Feedback Loop**:
   - Execute the targeted test suite against the change.
   - Read tracebacks, isolate regressions, and refine until all tests pass green.

> **Completion criterion**: Minimal code diff implemented; 100% of targeted and regression tests passing green.

---

## 5. Adversarial Review & Clean-Up Commit

Cut through polite AI praise by running harsh adversarial code reviews and clean-up audits:

```
┌─────────────────────────────────────────────────────────────┐
│                 THE ADVERSARIAL REVIEW RUBRIC               │
├─────────────────────────────────────────────────────────────┤
│ 1. Harsh Severity Scale: Grade the diff from 1 (broken) to  │
│    10 (bulletproof). Assume adversarial production traffic. │
│ 2. Failure Mode Hunt: Identify uncaught exceptions, leaks,  │
│    missing index joins, race conditions, or silent errors.  │
│ 3. Actionable Git Diff: Provide exact patch diffs to fix    │
│    every identified flaw immediately.                       │
└─────────────────────────────────────────────────────────────┘
```

1. **Execute Harsh Adversarial Review**:
   - Review the final diff against the 8-point checklist:
     - [ ] Did it solve the exact problem requested?
     - [ ] Did it change unrelated behavior?
     - [ ] Did it add unnecessary abstraction?
     - [ ] Did it introduce security or permission vulnerabilities?
     - [ ] Did it hide/swallow errors instead of handling them?
     - [ ] Did it update all relevant tests?
     - [ ] Did it follow project conventions?
     - [ ] Can the diff be made smaller and simpler?
2. **Clean-Up Commit Audit**:
   - Hunt for left-over `TODO`, `FIXME`, debugging `print()` statements, and unhandled edge cases.
   - Strip all debugging debris before finalizing.

> **Completion criterion**: Adversarial review completed with severity scoring, zero debugging debris remaining, and clean-up commit ready.

---

## In-File Reference: The 5 Must-Run Verification Prompts

### Prompt 1: The Adversarial Reviewer
```markdown
Review this git diff critically on a scale of 1 to 10. Do not give polite compliments.
Act as an uncompromising principal engineer hunting for production outages, race conditions,
swallowed exceptions, unindexed queries, and subtle edge-case failures.
For every issue found, explain why it will fail and provide the exact git diff to fix it.
```

### Prompt 2: The DAG Seam Hunter
```markdown
Analyze the components touched in this change as a Directed Acyclic Graph (DAG).
Identify all component seams (boundaries between modules, network interfaces, and database writes).
Generate a prioritized table of the 3 most critical edge-case failure modes at these seams
and output the test code required to verify them.
```

### Prompt 3: The Edge-Case & Clean-Up Hunter
```markdown
Inspect the current branch for:
1. Forgotten TODO or FIXME comments.
2. Debugging logs or console prints left behind.
3. Edge cases on non-happy paths that lack unit test coverage.
Output a clean-up checklist and provide the exact tests for any missing edge cases.
```

---

## Anti-Patterns

- **Polite Rubber-Stamping** — Accepting pleasant LLM responses ("Looks great, clean code!") without demanding failure mode analysis.
- **Shotgun Editing** — Modifying multiple files across the codebase before inspecting the repository architecture.
- **Moving the Goalposts (Test Mutation)** — Modifying test assertions to make a flawed implementation pass instead of fixing the code.
- **Debugging Debris Pollution** — Leaving temporary print statements, comments, or commented-out code in final commits.
- **Speculative Complexity** — Introducing complex design patterns or unrequested dependencies for simple bug fixes.
