```
┌────────────────────────────────────────────────────────┐
│             SKILL: legacy-refactoring-guardian         │
├────────────────────────────────────────────────────────┤
│ Name:        legacy-refactoring-guardian               │
│ Category:    software_engineering                      │
│ Domain:      Software Engineering / Modernization      │
│ Invocation:  /legacy-refactoring-guardian              │
│ Triggers:    "refactor legacy code", "code archaeology",│
│              "characterization tests", "legacy safety", │
│              "introduce seam", "capture behavior"      │
│ Version:     1.1.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.legacy_refactoring_guardian"     │
├────────────────────────────────────────────────────────┤
│ Target:      Deterministic AST codebase archaeology,   │
│              automated characterization test generator, │
│              and micro-step legacy refactoring engine. │
└────────────────────────────────────────────────────────┘
```

# Legacy Refactoring Guardian — Companion Summary Card

`legacy-refactoring-guardian` enforces rigorous codebase archaeology, temporary characterization test safety nets, and disciplined micro-step refactoring loops before modifying legacy or untested systems.

See [SKILL.md](SKILL.md) for the complete 5-stage operational specification.
Consult `references/seam-catalog.md` for seam patterns and `examples/legacy-billing-service/` for a runnable modernization exemplar.
Related skills: `/crafting-skills` for skill standards, `/adversarial-agent-verifier` for seam verification, and `/deepen-architecture` for architecture deepening.

---

## 5-Stage Progression Table

| Stage | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Repository Mapping & Capability Scoping** | Map landscape and isolate exactly 1 business capability | Architectural inventory & capability boundary | `Single capability isolated` |
| **Stage 2: Execution Tracing & Seam Identification** | Trace end-to-end flow via AST, catalog contracts, prepare seams | `scripts/legacy_archaeologist.py` trace | `5-level evidence validated` |
| **Stage 3: The Visual Forge Brief** | Synthesize archaeology, contracts, and unknowns into interactive visual brief | `%TEMP%\legacy-refactoring-guardian-<timestamp>.html` | `Visual brief generated` |
| **Stage 4: Checkpoint & Characterization Harness** | Synthesize characterization tests capturing ground truth without hallucination | `scripts/char_test_harness.py` emitted suite | `Existing behavior green` |
| **Stage 5: Micro-Refactoring & Maturation** | Execute single structural steps, quarantine defects, and graduate tests | Refactored module & specification tests | `Zero behavioral regressions` |

---

## Bundled Tooling Seams

1. **AST Codebase Archaeologist (`scripts/legacy_archaeologist.py`)**:
   - `python scripts/legacy_archaeologist.py --file <path> --function <func>` — Extracts parameters, call sites, side effects, and complexity.
   - Flags: `--contracts`, `--seams`, `--mermaid`, `--json`.

2. **Deterministic Characterization Harness Generator (`scripts/char_test_harness.py`)**:
   - `python scripts/char_test_harness.py --file <path> --func <func> --emit <out_test.py>` — Generates boundary inputs, executes live code, and emits runnable `pytest` test suites with zero hallucination.

3. **Modernization Configuration (`config.default.yaml`)**:
   - Tunable boundary test sets, evidence search limits, and defect quarantine policies.

---

## The Three Foundational Craft Pillars

1. **The Visual Brief Pillar**:
   - Every legacy modernization initiative generates an interactive HTML visual brief in `%TEMP%\legacy-refactoring-guardian-<timestamp>.html`.
   - Incorporates Capability Execution DAGs, Contracts & Side Effects matrices, and the Unknowns Registry.

2. **The Mandatory Checkpoint Gate Pillar**:
   - Freezes autonomous execution after archaeology and before refactoring.
   - Authors `implementation_plan.md` with `RequestFeedback: true` to align on test boundaries, observable side effects, and known anomalies.

3. **The Anti-Pattern Defense Pillar**:
   - Strictly enforces defenses against Inventing Expected Behavior, Premature Target Architecture, Freezing Implementation Details, and Stealth Bug Fixing.
   - Formatted strictly under `## Anti-Patterns` with `- **Name** — Description`.

---

## 5-Level Evidence Validation Hierarchy

When AI asserts a fact about legacy code, validate against this descending hierarchy:
1. **Repository Search & AST**: Confirm call sites, invocations, and references via `rg`.
2. **Existing Tests**: Inspect fixtures, test cases, and edge assertions for historical assumptions.
3. **Database Schema**: Verify nullability, foreign keys, default values, and column naming.
4. **Logs & Telemetry**: Confirm if code paths are actively invoked in production.
5. **Git Version History**: Use `git log -S` and `git blame` to reveal why unusual code was introduced.

---

## Verification Checklist

- [ ] Modernization bounded strictly to 1 business capability.
- [ ] Execution path traced via `legacy_archaeologist.py`: Input $\rightarrow$ Logic $\rightarrow$ State Mutations $\rightarrow$ Side Effects $\rightarrow$ Output.
- [ ] Implicit contracts cataloged (APIs, events, DB, CSVs, logs).
- [ ] Mechanical seams created without redesigning business domain logic.
- [ ] Characterization test suite generated via `char_test_harness.py` from executable ground truth.
- [ ] Observable side effects (DB writes, events, queues) asserted.
- [ ] Apparent defects characterized as-is and quarantined from refactoring.
- [ ] Refactor executed one structural change at a time with instant test verification.
