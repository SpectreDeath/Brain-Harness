# Context Lint Cleanup Plan (2026-11-06-1950-EST)

## Goal

Harden `src/harness/services/codebase_context/` by recording complete pass diagnostics across all scanned context and script checks, eliminating over-broad archetype suffix exemptions that mask broken documentation paths, and reconciling the Rule 11 token budget configuration against the IDE 24 KB rule truncation boundary.

## Starting Facts & Architecture Seams

- **File 1**: `src/harness/services/codebase_context/linter.py` (185 lines).
  - Defect 1: `ContextLinter.run_lint` only records `PathIntegrityCheck`, `ScriptIntegrityCheck`, and `SyncDriftCheck` objects upon failure, misleadingly reporting `Context files healthy across 3 checks` (counting only token budget checks) rather than reflecting the 76 scanned files and 347 path spans.
- **File 2**: `src/harness/services/codebase_context/classifier.py` (69 lines).
  - Defect 2: `is_archetype_template` extracts `span.split("/")[-1]` and matches against `ARCHETYPE_FILENAMES`, silently exempting non-existent paths ending in `config.yaml`, `drift.json`, `main.py`, etc.
- **File 3**: `src/harness/services/codebase_context/config.py` (66 lines) and `.agents/skills.config.yaml`.
  - Defect 3: `.agents/skills.config.yaml` overrides `AGENTS.md` token budget to `8,000` tokens, while `AGENTS.md` currently stands at `6,808` tokens / `27,230` bytes, triggering IDE 24 KB rule truncation.
- **Constraint**: Rule 11 strict 200-line ceiling across `src/harness/services/codebase_context/`.

---

## Track 1 — Linter Diagnostic Completeness (`linter.py`)

- [ ] **1.1** Failing test contract: Author unit test in `tests/test_codebase_context_linter.py` asserting that passing runs record positive diagnostics for path, script, and drift checks rather than solely token budgets.
- [ ] **1.2** Comprehensive check recording: Update `ContextLinter.run_lint` to append passed diagnostic checks for file paths, scripts, and sync drift when no violations are detected.
- [ ] **1.3** Accurate CLI check summary: Ensure `harness context lint` output accurately reflects the total number of files and semantic invariant checks evaluated.
- [ ] **1.4** Rule 11 verification: Assert `linter.py` remains strictly $\le 200$ lines, factoring out any reporting helpers into a sibling submodule if needed.

---

## Track 2 — Path Classifier Tightening & Broken Path Repair (`classifier.py`)

- [ ] **2.1** Failing test contract: Author unit test asserting that multi-segment non-existent paths ending in archetype filenames (e.g. `scratch/drift.json`, `foo/bar/main.py`) are flagged as invalid rather than exempted.
- [ ] **2.2** Restrict archetype template matching: Update `is_archetype_template` to exempt filenames only when bare (`"/" not in span`) or containing explicit template placeholders (`<...>`, `*`, `{...}`).
- [ ] **2.3** Repair newly revealed broken doc links: Audit and repair genuine broken references across repository markdown files revealed by tightened classification.
- [ ] **2.4** Rule 11 verification: Assert `classifier.py` remains strictly $\le 200$ lines.

---

## Track 3 — Token Budget Governance & Configuration Reconciliation

- [ ] **3.1** Configuration audit: Reconcile `.agents/skills.config.yaml` overrides against `DEFAULT_TOKEN_BUDGETS` in `config.py` and document budget rationale.
- [ ] **3.2** IDE truncation boundary guard: Establish an enforceable threshold preventing context rule files from exceeding the 24,000-byte IDE system prompt truncation limit.

---

## Track 4 — Verification & Governance

- [ ] **4.1** Unit test suite pass: Run `pytest tests/test_codebase_context*.py` and verify all tests pass.
- [ ] **4.2** Clean context lint verification: Run `harness context lint` and confirm zero false-positive errors and full diagnostic reporting.
- [ ] **4.3** Line count audit: Verify that all files in `src/harness/services/codebase_context/` strictly satisfy $\le 200$ lines.
- [ ] **4.4** Independent check: Independent verification of all 13 prior checkboxes with execution evidence before sign-off.
